import argparse
import logging
from helper.gateway import portal
from helper.utils import pathfinder
log = logging.getLogger(__name__)
pf = pathfinder()
p = portal()  


class base_extension():

    def get(self):
        data_list = p.get_many(self.ext)
        pf.save_to_file(self.ext , data_list)

    def post(self):    
        data_list= pf.get_input('post', self.ext)
        for data in data_list:
            clean_data = self.get_clean_data(data)
            p.post_one(self.ext, clean_data)
    
    def delete(self):    
        data_list= pf.get_input('delete', self.ext)
        for data in data_list:
            #cmnt: If id in not present in data then look for other key for search.
            #This will be used toget id to post data
            if (data_id := data.get('id')) is None:
                query_1 = {}
                        #cmnt: get lsit if feilds that can be used  as key to post data. 
                for key in self.data_prim_keys:
                    key_val = data.get(key, None)
                    if key_val is not None:
                        query_1[key] = key_val
                        break
                if not query_1:
                    log.error(f'Can find refrence id or name or description of ext to update')
                    continue
                #cmnt: get as many data for extension this will be used toget id to post data
                exts = p.get_many(self.ext, query = query_1)
                log.debug(f'log: {exts=}')
                if isinstance(exts, list) and len(exts) > 0:
                    log.debug(f'Got {exts[0]=}')
                    data_id  = exts[0].get('id')
                else:
                    log.error(f'can not find the {self.ext=} id in {query_1=}')
                    continue
            p.delete_one(self.ext, data_id)

    def patch(self):
        data_list = pf.get_input('patch', self.ext)
        for data in data_list:
            #cmnt: If id in not present in data then look for other key for search.
            #This will be used toget id to post data
            if (data_id := data.get('id')) is None:
                query_1 = {}
                        #cmnt: get lsit if feilds that can be used  as key to post data. 
                for key in self.data_prim_keys:
                    key_val = data.get(key, None)
                    if key_val is not None:
                        query_1[key] = key_val
                        break
                if not query_1:
                    log.error(f'Can find refrence id or name or description of ext to update')
                    continue
                #cmnt: get as many data for extension this will be used toget id to post data
                exts = p.get_many(self.ext, query = query_1)
                log.debug(f'log: {exts=}')
                if isinstance(exts, list) and len(exts) > 0:
                    log.debug(f'Got {exts[0]=}')
                    data_id  = exts[0].get('id')
                else:
                    log.error(f'can not find the {self.ext=} id in {query_1=}')
                    continue
            clean_data = self.get_clean_data(data)
            p.patch_one(self.ext, data_id, clean_data)

    def search_manager(self, query_string ):
        ext = f'search/{self.ext}'
        query_1 = {'query_string': query_string} 
        search_results = p.get_many(ext, query = query_1) 
        log.debug(search_results)
        return search_results
    
class groups(base_extension):
    def __init__(self, ext : str = 'group' ):
        self.ext = ext
        self.supported_mode = 'get post patch delete'.split()
        #for Post and patch
        self.valid_columns = 'name description type members'.split()
        self.data_prim_keys = 'name description'.split()   

    #doc def get_clean_data(self,data): prepare data to send for upload
    def get_clean_data(self, data):
        #doc this apply only for host
        if data.get('members', None) is not None:
            if not isinstance(data['members'], list): 
                data['members'] = data.get('members').split(',')
        else:
            data['memeber'] = []
        if data['type'] == 'host' and (memebers_names_str := data.get('member_name', None)) is not None:
            memeber_ids = []
            memebers_names = memebers_names_str.split(',')

            for memeber_name in memebers_names:
                name_ids = []
                memeber_name = memeber_name.strip()
                query_string = f'host.name:"{memeber_name}"'
                log.info(query_string)
                hst = getter('hosts')
                name_members = hst.search_manager(query_string )
                if name_members is None or len(name_members) < 1:
                    log.error(f'member result no sutable:{name_members}')
                    continue
                for name_member in name_members:
                    name_ids.append(name_member['id'])
                memeber_ids.extend(name_ids)
            memeber_ids = list(set(memeber_ids))
            data['members'].extend(memeber_ids)
        clean_data = {key: data[key] for key in self.valid_columns}       
        return clean_data
        

class rules(base_extension):
    def __init__(self, ext : str = 'group' ):
        self.ext = ext
        self.supported_mode = 'get post patch delete'.split()
        #for Post and patch
        self.valid_columns = 'name description type members'.split()
        self.data_prim_keys = 'name description'.split()   

class getter(base_extension):
    def __init__(self, ext):
        self.ext = ext
        self.supported_mode = 'get'.split()


class cls_ext_map():
    def __init__(self) -> None:
        getter_exts = 'accounts assignments assignment_outcomes audits campaigns detections \
                 health hosts ip_addresses lockdown/account lockdown/host proxies rules search \
                 sensor_token settings subnets tagging threatFeeds traffic usage/detect users \
                 vectramatch/enablement vectra-match/status vectramatch/availabledevices vectra-match/rules \
                  vectramatch/assignment vectra-match/alertstats vsensor'.split()
        
        self.cls_exts = {getter : getter_exts,
                         groups : ['groups'],  
                         }
        
    def get_cls(self,ext : str ):
        for k,v in self.cls_exts.items():
            if ext in v:
                return k
        return None
            
    def all_exts(self) -> list:
        ext_list = []
        for exts in self.cls_exts.values():        
            ext_list.extend(exts) 
        ext_list.sort()
        return ext_list

