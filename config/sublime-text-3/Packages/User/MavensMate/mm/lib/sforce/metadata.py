# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# Written by: David Lanstein ( dlanstein gmail com )

from base import SforceBaseClient
import mm.xmltodict as xmltodict
import time
import mm.util as util
import mm.config as config
from mm.exceptions import *
import shutil
import os
from operator import itemgetter

debug = config.logger.debug

class SforceMetadataClient(SforceBaseClient):

    def __init__(self, wsdl, *args, **kwargs):
        kwargs['isMetadata'] = True
        super(SforceMetadataClient, self).__init__(wsdl, *args, **kwargs)
        header = self.generateHeader('SessionHeader')
        header.sessionId = kwargs['sid']
        self.setSessionHeader(header)
        self._setEndpoint(kwargs['url'])
        self._setHeaders('')

    def retrieve(self, **kwargs):
        # request = {
        #   'RetrieveRequest': {
        #     'unpackaged': {
        #       'types': {
        #         'ApexTrigger': '*'
        #       }
        #     },
        #     'apiVersion': {
        #       25.0
        #     }
        #   }
        # }
        # package = {
        #     'unpackaged' : {
        #         'types' : [
        #             {
        #                 "members": "*",
        #                 "name": "ApexClass"
        #             }
        #         ]
        #     }
        # }
        package_dict = None
        request_payload = None

        debug('retrieve request: ')
        debug(kwargs['package'])

        if 'package' in kwargs and type(kwargs['package']) is not dict:
            #if package is location of package.xml, we'll parse the xml and create a request
            package_dict = xmltodict.parse(util.get_file_as_string(kwargs['package']))
            api_version = package_dict['Package']['version']
            package_dict['unpackaged'] = package_dict.pop('Package')
            package_dict['unpackaged'].pop('version')
            package_dict['unpackaged'].pop("@xmlns", None)
            package_dict['unpackaged'].pop("#text", None)
            package_dict['apiVersion'] = api_version
            types = package_dict['unpackaged']['types']
            if type(types) is not list:
                types = [types]
            if type(package_dict['unpackaged']['types']) is not list:
                package_dict['unpackaged']['types'] = [package_dict['unpackaged']['types']]
            requested_types = []
            if 'type' in kwargs and kwargs['type'] != None and kwargs['type'] != '': #if the request is for a certain type, only request that type
                for i, val in enumerate(types):
                    if val['name'] == kwargs['type']:
                        requested_types.append(val)
                package_dict['unpackaged']['types'] = requested_types
                types = requested_types
            for i, val in enumerate(types):
                try:
                    package_dict['unpackaged']['types'][i].pop("#text", None)
                except:
                    package_dict['unpackaged']['types'].pop("#text", None)

            #if custom object is asterisked, we need to explictly retrieve standard objects
            for t in package_dict['unpackaged']['types']:
                if 'name' in t:
                    metadata_type_def = util.get_meta_type_by_name(t['name'])
                    if metadata_type_def is not None and 'inFolder' in metadata_type_def and metadata_type_def['inFolder']: #TODO: right now this skips retrieval of unknown types, we should use describe data
                        if 'members' in t and type(t['members']) is not list:
                            if t['members'] == "*" or t['members'] == []:
                                mlist = self.listMetadata(t['name'], False)
                                objs = []
                                for obj in mlist:
                                    objs.append(obj['fullName'])
                                objs.sort()
                                t['members'] = objs
                    elif t['name'] == 'CustomObject':
                        if 'members' in t and type(t['members']) is not list:
                            if t['members'] == "*":
                                mlist = self.listMetadata('CustomObject', False)
                                objs = []
                                for obj in mlist:
                                    if ('__c') not in mlist:
                                        objs.append(obj['fullName'])
                                objs.append("*")
                                objs.sort()
                                t['members'] = objs

            request_payload = package_dict

        elif 'package' in kwargs and type(kwargs['package']) is dict:
            package = kwargs['package']
            if package == {}:
                raise MMException('Invalid package')
            if 'unpackaged' not in package:
                #{ "ApexClass"    : ["MultiselectControllerTest","MultiselectController"] }
                type_array = []
                for i, metadata_type in enumerate(package):
                    member_value = package[metadata_type]
                    type_array.append({ "name" : metadata_type, "members" : member_value })

                package = {
                    'unpackaged' : {
                        'types' : type_array
                    },
                    'apiVersion' : util.SFDC_API_VERSION
                }

            #if custom object is asterisked, we need to explictly retrieve standard objects
            for t in package['unpackaged']['types']:
                debug('----> ')
                debug(t)
                if 'name' in t:
                    metadata_type_def = util.get_meta_type_by_name(t['name'])
                    debug(metadata_type_def)
                    if metadata_type_def is not None and 'inFolder' in metadata_type_def and metadata_type_def['inFolder']: #TODO: right now this skips retrieval of unknown types, we should use describe data
                        if 'members' in t and (t['members'] == "*" or t['members'] == []):
                            #list_request_name = self.__transformFolderMetadataNameForListRequest(t['name'])
                            #mlist = self.listMetadata(list_request_name, False)
                            mlist = self.listMetadataAdvanced(t['name'])
                            objs = []
                            for obj in mlist:
                                debug('---obj')
                                debug(obj)
                                objs.append(obj['title'])
                                if 'children' in obj and type(obj['children'] is list):
                                    for child in obj['children']:
                                        objs.append(obj['title']+"/"+child['title'])
                            objs.sort()
                            t['members'] = objs
                    elif t['name'] == 'CustomObject':
                        if 'members' in t and type(t['members']) is not list:
                            if t['members'] == "*":
                                mlist = self.listMetadata('CustomObject', False)
                                objs = []
                                for obj in mlist:
                                    if ('__c') not in mlist:
                                        objs.append(obj['fullName'])
                                objs.append("*")
                                objs.sort()
                                t['members'] = objs

            request_payload = package
            debug('---request payload---')
            debug(request_payload)
        result = self._handleResultTyping(self._sforce.service.retrieve(request_payload))

        debug('result of retrieve: \n\n')
        debug(result)

        if result.done == False:
            debug('---> result is not done')
            if int(float(util.SFDC_API_VERSION)) > 30:
                return self._waitForRetrieveRequest(result.id) # will loop until done
            else:
                self._waitForRetrieveRequest(result.id) # will loop until done
                return self._getRetrieveBody(result.id)
        else:
            return result

        # if result.done == False:
        #     if int(float(util.SFDC_API_VERSION)) > 30:
        #         return self._waitForRetrieveRequest(result.id)
        #     else:
        #         return self._getRetrieveBody(result.id)
        # else:
        #     return result

    def deploy(self, params={}, **kwargs):
        if 'debug_categories' in params:
            self._setHeaders('deploy', debug_categories=params['debug_categories'])

        deploy_options = {}

        is_test = kwargs.get('is_test', False)
        if is_test:
            deploy_options['checkOnly']         = True
            deploy_options['runAllTests']       = False
            deploy_options['runTests']          = params.get('classes', [])
            deploy_options['rollbackOnError']   = params.get('rollback_on_error', True)
        else:
            deploy_options['checkOnly']         = params.get('check_only', False)
            deploy_options['rollbackOnError']   = params.get('rollback_on_error', True)
            deploy_options['runAllTests']       = params.get('run_tests', False)
            deploy_options['runTests']          = params.get('classes', [])
            deploy_options['purgeOnDelete']     = params.get('purge_on_delete', False)

        result = self._handleResultTyping(self._sforce.service.deploy(params['zip_file'], deploy_options))
        #config.logger.debug('deploy request')
        #config.logger.debug(self.getLastRequest())

        if result.done == False:
            self._waitForRequest(result.id)
            if 'ret_xml' in params and params['ret_xml'] == True:
                self._sforce.set_options(retxml=True)

            deploy_result = self._getDeployResponse(result.id)

            try:
                deploy_result['log'] = self.getDebugLog()
            except:
                pass

            self._sforce.set_options(retxml=False)

            return deploy_result
        else:
            try:
                deploy_result['log'] = self.getDebugLog()
            except:
                pass
            return result

    def listMetadata(self, metadata_type, retXml=True, version=26.0):
        # obj = { 'type': 'ApexClass' }
        # response = mclient.service.listMetadata(obj, 25.0)
        self._sforce.set_options(retxml=retXml)
        if type(metadata_type) is not dict and type(metadata_type) is not list:
            obj = { 'type' : metadata_type }
        else:
            obj = metadata_type
        list_result = self._handleResultTyping(self._sforce.service.listMetadata(obj, version))
        debug('list_result ------>')
        debug(list_result)
        self._sforce.set_options(retxml=False)
        if retXml == True:
            try:
                list_result_dict = xmltodict.parse(list_result,postprocessor=util.xmltodict_postprocessor)
                return list_result_dict['soapenv:Envelope']["soapenv:Body"]["listMetadataResponse"]["result"]
            except:
                return []
        return list_result

    def __transformFolderMetadataNameForListRequest(self, metadata_type):
        metadata_request_type = metadata_type+"Folder"
        if metadata_request_type == "EmailTemplateFolder":
            metadata_request_type = "EmailFolder"
        return metadata_request_type

    def listMetadataAdvanced(self, metadata_type):
        try:
            metadata_type_def = util.get_meta_type_by_name(metadata_type)
            if metadata_type_def == None:
                return []
            has_children_metadata = False
            if 'childXmlNames' in metadata_type_def and type(metadata_type_def['childXmlNames']) is list:
                has_children_metadata = True
            is_folder_metadata = 'inFolder' in metadata_type_def and metadata_type_def['inFolder']
            if is_folder_metadata == True:
                metadata_request_type = self.__transformFolderMetadataNameForListRequest(metadata_type)
            else:
                metadata_request_type = metadata_type
            list_response = self.listMetadata(metadata_request_type, True, util.SFDC_API_VERSION)
            debug('--------------->')
            debug(list_response)
            if type(list_response) is not list:
                list_response = [list_response]
            #print list_response
            object_hash = {} #=> {"Account" => [ {"fields" => ["foo", "bar"]}, "listviews" => ["foo", "bar"] ], "Contact" => ... }

            if has_children_metadata == True and len(list_response) > 0: #metadata objects like customobject, workflow, etc.
                request_names = []
                for element in list_response:
                    #if element['fullName'] != 'PersonAccount':
                    request_names.append(element['fullName'])
                retrieve_result = self.retrieve(package={
                    metadata_request_type : request_names
                })
                #print '>>>> ',retrieve_result
                tmp = util.put_tmp_directory_on_disk()
                util.extract_base64_encoded_zip(retrieve_result.zipFile, tmp)

                #iterate extracted directory
                for dirname, dirnames, filenames in os.walk(os.path.join(tmp,"unpackaged",metadata_type_def['directoryName'])):
                    for f in filenames:
                        #f => Account.object
                        full_file_path = os.path.join(dirname, f)
                        data = util.parse_xml_from_file(full_file_path)
                        c_hash = {}
                        for child_type in metadata_type_def['childXmlNames']:
                            child_type_def = util.get_meta_type_by_name(child_type)
                            if child_type_def == None: #TODO handle newer child types
                                continue
                            tag_name = child_type_def['tagName']
                            items = []
                            try:
                                if tag_name in data[metadata_request_type]:
                                    if type(data[metadata_request_type][tag_name]) is not list:
                                        data[metadata_request_type][tag_name] = [data[metadata_request_type][tag_name]]
                                    for i, val in enumerate(data[metadata_request_type][tag_name]):
                                        items.append(val['fullName'])
                            except BaseException, e:
                                #print 'exception >>>> ', e.message
                                pass

                            c_hash[tag_name] = items

                        base_name = f.split(".")[0]
                        object_hash[base_name] = c_hash

                shutil.rmtree(tmp)
            #print '>>> ',object_hash
            return_elements = []
            for element in list_response:
                if config.connection.get_plugin_client_setting('mm_ignore_managed_metadata') == True:
                    if 'manageableState' in element and element["manageableState"] != "unmanaged":
                        continue

                children = []
                full_name = element['fullName']
                #if full_name == "PersonAccount":
                #    full_name = "Account"
                #print 'processing: ', element
                if has_children_metadata == True:
                    if not full_name in object_hash:
                        continue
                    object_detail = object_hash[full_name]
                    if object_detail == None:
                        continue

                    for child in metadata_type_def['childXmlNames']:
                        child_type_def = util.get_meta_type_by_name(child)
                        if child_type_def == None: #TODO: handle more complex types
                            continue
                        tag_name = child_type_def['tagName']
                        if len(object_detail[tag_name]) > 0:
                            gchildren = []
                            for gchild_el in object_detail[tag_name]:
                                gchildren.append({
                                    "text"      : gchild_el,
                                    "isFolder"  : False,
                                    "checked"   : False,
                                    "level"     : 4,
                                    "leaf"      : True,
                                    "id"        : metadata_type_def['xmlName']+"."+full_name+"."+tag_name+"."+gchild_el,
                                    "select"    : False,
                                    "title"     : gchild_el
                                })
                                children = sorted(children, key=itemgetter('text'))

                            children.append({
                                "text"      : child_type_def['tagName'],
                                "isFolder"  : True,
                                "cls"       : "folder",
                                "children"  : gchildren,
                                "checked"   : False,
                                "level"     : 3,
                                "id"        : metadata_type_def['xmlName']+"."+full_name+"."+tag_name,
                                "select"    : False,
                                "title"     : child_type_def['tagName']
                            })

                #if this type has folders, run queries to grab all metadata in the folders
                if is_folder_metadata == True:
                    if config.connection.get_plugin_client_setting('mm_ignore_managed_metadata', True):
                        if 'manageableState' in element and element["manageableState"] != "unmanaged":
                            continue
                    #print element["fullName"]
                    list_request = {
                        "type"      : metadata_type,
                        "folder"    : element["fullName"]
                    }
                    list_basic_response = self.listMetadata(list_request, True, config.connection.sfdc_api_version)

                    if type(list_basic_response) is not list:
                        list_basic_response = [list_basic_response]

                    for folder_element in list_basic_response:
                        children.append({
                            "text"      : folder_element['fullName'].split("/")[1],
                            "leaf"      : True,
                            "isFolder"  : False,
                            "checked"   : False,
                            "level"     : 3,
                            "id"        : folder_element['fullName'].replace('/', '.'),
                            "select"    : False,
                            "title"     : folder_element['fullName'].split("/")[1]

                        })

                children = sorted(children, key=itemgetter('text'))
                is_leaf = True
                cls = ''
                if is_folder_metadata:
                    is_leaf = False
                    cls = 'folder'
                if has_children_metadata:
                    is_leaf = False
                    cls = 'folder'
                if metadata_type_def['xmlName'] == 'Workflow':
                    is_leaf = True
                    cls = ''
                #print '>>> ',element
                return_elements.append({
                    "text"      : element['fullName'],
                    "isFolder"  : is_folder_metadata or has_children_metadata,
                    "cls"       : cls,
                    "leaf"      : is_leaf,
                    "children"  : children,
                    "checked"   : False,
                    "level"     : 2,
                    "id"        : metadata_type_def['xmlName']+'.'+full_name.replace(' ', ''),
                    "select"    : False,
                    "title"     : element['fullName']
                })

            return_elements = sorted(return_elements, key=itemgetter('text'))
            # if list_response == []:
            #     return list_response

            # return list_response
            return return_elements
        except BaseException, e:
            debug('exception')
            debug(e)
            if 'INVALID_TYPE: Unknown type' in e.message:
                return None
            else:
                raise e


    def getOrgNamespace(self):
        describe_result = self.describeMetadata(retXml=False)
        return describe_result.organizationNamespace or ''

    def describeMetadata(self, **kwargs):
        retXml = kwargs.get('retXml', True)
        self._sforce.set_options(retxml=retXml)
        api_version = kwargs.get('api_version', util.SFDC_API_VERSION)
        metadata_result = self._sforce.service.describeMetadata(api_version)
        self._sforce.set_options(retxml=False)
        return metadata_result

    def _getDeployResponse(self, id):
        if int(float(util.SFDC_API_VERSION)) >= 29:
            return self._handleResultTyping(self._sforce.service.checkDeployStatus(id, True))
        else:
            return self._handleResultTyping(self._sforce.service.checkDeployStatus(id))

    def _getRetrieveBody(self, id):
        return self._handleResultTyping(self._sforce.service.checkRetrieveStatus(id))

    def _waitForRetrieveRequest(self, id):
        debug('waiting for retrieve request ...')
        finished = False
        checkStatusResponse = None
        while finished == False:
            time.sleep(1)
            if int(float(util.SFDC_API_VERSION)) <= 30:
                checkStatusResponse = self._sforce.service.checkStatus(id)
                finished = checkStatusResponse[0].done
                if finished:
                    return None
            else: #api 31.0 and greeater
                checkStatusResponse = self._sforce.service.checkRetrieveStatus(id)
                debug('checkStatusResponse --->')
                debug(checkStatusResponse)
                finished = checkStatusResponse.success
                if finished:
                    return checkStatusResponse

    def _waitForRequest(self, id):
        finished = False
        checkStatusResponse = None
        while finished == False:
            time.sleep(1)
            if int(float(util.SFDC_API_VERSION)) >= 29:
                checkStatusResponse = self._sforce.service.checkDeployStatus(id, True)
                finished = checkStatusResponse.done
            else:
                checkStatusResponse = self._sforce.service.checkStatus(id)
                finished = checkStatusResponse[0].done

    # SOAP header-related calls (debug options?)
    def setCallOptions(self, header):
        '''
        This header is only applicable to the Partner WSDL
        '''
        self._callOptions = header
