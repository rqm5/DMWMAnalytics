#!/usr/bin/env python
#-*- coding: utf-8 -*-
#pylint: disable=
"""
File       : dbs.py
Author     : Valentin Kuznetsov <vkuznet AT gmail dot com>
Description: DBS service module
"""
from __future__ import print_function

# system modules
import time
import hashlib
from   types import InstanceType

# pymongo modules
from pymongo import DESCENDING

# package modules
import DCAF.utils.jsonwrapper as json
from DCAF.utils.utils import dates_from_today, genkey
from DCAF.services.generic import GenericService

class DBSService(GenericService):
    """
    Helper class to provide DBS service
    """
    def __init__(self, config=None, verbose=0):
        GenericService.__init__(self, config, verbose)
        self.name = 'dbs'
        self.url = config['services'][self.name]
        self.instances = ["prod/phys01", "prod/phys02", "prod/phys03"]
        self.all_dbs = ['prod/global']+self.instances
        self.tiers = set() # fill at run time

    def fetch(self, api, params=None, dbsinst='prod/global', cache=True):
        "Fetch data for given api"
        if  dbsinst:
            dbs_url = self.url.replace('prod/global', dbsinst)
        inst = {'dbs_instance':self.all_dbs.index(dbsinst)}
        if  api == 'releases':
            url = '%s/releaseversions' % dbs_url
        else:
            url = '%s/%s' % (dbs_url, api)
        data = json.loads(super(DBSService, self).fetch(url, params, cache))
        if  api == 'releases':
            data = data[0]['release_version']
        for row in data:
            if  api == 'datasets':
                try:
                    row['rid'] = row['dataset_id']
                except KeyError:
                    print("Unable to process dataset row", row)
                    if  'dataset' in row:
                        h = hashlib.md5()
                        h.update(row['dataset'])
                        row['rid'] = int(h.hexdigest()[:10], 16)
                        print("Generated new dataset_id", row['dataset'], h.hexdigest(), row['rid'])
                except:
                    print("Unable to process dataset row", row)
                    raise
                row.update(inst)
                yield row
            elif api == 'releases':
                rid = genkey(row, truncate=5)
                rec = {'release':row, 'rid':rid}
                yield rec
            elif api == 'filesummaries':
                yield row
            else:
                yield row

    def update(self, cname):
        "Update internal database with fresh snapshot of data"
        if  self.verbose:
            print("%s update %s" % (self.name, cname))
        self.storage.cleanup(cname)
        if  cname == 'datasets':
            spec = {'dataset':'/*/*/*', 'detail':'true'}
            for dbsinst in self.all_dbs:
                docs = self.fetch(cname, spec, dbsinst, cache=False)
                self.storage.insert('datasets', docs)
            index_list = [('dataset', DESCENDING), ('rid', DESCENDING), ('dataset_id', DESCENDING)]
            self.storage.indexes('datasets', index_list)
        elif cname == 'releases':
            docs = self.fetch(cname, cache=False)
            self.storage.insert(cname, docs)
            index_list = [('release', DESCENDING), ('rid', DESCENDING)]
            self.storage.indexes('releases', index_list)

    def datasets(self):
        "Return list of datasets"
        spec = {}
        for row in self.storage.fetch('datasets', spec):
            yield row['dataset']

    def new_datasets(self, ndays=7):
        "Return list of new datasets"
        cdate1, cdate2 = dates_from_today(ndays)
        spec = {'dataset':'/*/*/*', 'detail':'true',
                'min_cdate':int(cdate1), 'max_cdate':int(cdate2)}
        for row in self.fetch('datasets', spec):
            rec = {'dataset':row['dataset'], 'dataset_id':row['dataset_id']}
            yield rec

    def releases(self):
        "Return list of releases"
        spec = {}
        for row in self.storage.fetch('releases', spec):
            yield row

    def dataset_info(self, dataset, dbsinst=None):
        "Return list of datasets"
        api = 'datasets'
        spec = {'dataset':dataset}
        res = [r for r in self.storage.fetch(api, spec)]
        if  not len(res):
            # look-up dataset in other DBS instances
            spec.update({'detail':'true'})
            if  dbsinst:
                res = [r for r in self.fetch(api, spec, dbsinst)]
                if  len(res):
                    return res[0]
            for dbsinst in self.all_dbs:
                res = [r for r in self.fetch(api, spec, dbsinst)]
                if  len(res):
                    return res[0]
            return None
        else:
            return res[0]

    def dataset_summary(self, dataset, dbsinst=None):
        "Return dataset summary"
        # TODO, store dataset summary into analytics db
        api = 'filesummaries'
        spec = {'dataset':dataset}
        res = [r for r in self.fetch(api, spec, dbsinst)]
        if  not len(res):
            # look-up dataset in other DBS instances
            for dbsinst in self.all_dbs:
                res = [r for r in self.fetch(api, spec, dbsinst)]
                if  len(res):
                    return res[0]
            # so far, return zeros
            return {'num_file':0, 'num_lumi':0, 'num_block':0, 'num_event':0, 'file_size':0}
        else:
            return res[0]

    def dataset_parents(self, dataset, dbsinst=None):
        "Return dataset id of the parent"
        api = 'datasetparents'
        spec = {'dataset': dataset}
        for row in self.fetch(api, spec, dbsinst):
            yield row['parent_dataset_id']

    def dataset_release_versions(self, dataset, dbsinst=None):
        "Return dataset release versions"
        url = '%s/releaseversions' % self.url
        params = {'dataset':dataset}
        dbs_url = url.replace('prod/global', dbsinst)
        data = json.loads(super(DBSService, self).fetch(dbs_url, params))
        if  not len(data) or not 'release_version' in data[0]:
            for dbsinst in self.all_dbs:
                dbs_url = url.replace('prod/global', dbsinst)
                data = json.loads(super(DBSService, self).fetch(dbs_url, params))
                if  len(data) and 'release_version' in data[0]:
                    break
        if  data and isinstance(data, list) and len(data) > 0:
            if  'release_version' in data[0]:
                for ver in set(data[0]['release_version']):
                    yield ver
            else:
                yield "N/A"
        else:
            yield "N/A"

    def dataset_dbsinst(self, dataset):
        "Find dbsinstance of given dataset"
        url = '%s/datasets' % self.url
        params = {'dataset': dataset}
        for dbsinst in self.all_dbs:
            dbs_url = url.replace('prod/global', dbsinst)
            data = json.loads(super(DBSService, self).fetch(dbs_url, params))
            if  len(data) and 'dataset' in data[0] and data[0]['dataset'] == dataset:
                return dbsinst

    def data_tiers(self):
        "Return list of known data-tiers"
        if  self.tiers:
            return self.tiers
        url = '%s/datatiers' % self.url
        params = {}
        for dbsinst in self.all_dbs:
            dbs_url = url.replace('prod/global', dbsinst)
            data = json.loads(super(DBSService, self).fetch(dbs_url, params))
            for tdict in data:
                self.tiers.add(tdict['data_tier_name'])
        return self.tiers
