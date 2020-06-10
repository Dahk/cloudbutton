import os
import json
import logging
import importlib
from cloudbutton.version import __version__
from cloudbutton.engine.config import CACHE_DIR, RUNTIMES_PREFIX, JOBS_PREFIX, TEMP_PREFIX
from cloudbutton.engine.utils import is_cloudbutton_function, uuid_str
from cloudbutton.engine.storage.utils import create_status_key, create_output_key, \
    status_key_suffix, init_key_suffix, CloudObject, StorageNoSuchKeyError

logger = logging.getLogger(__name__)


class Storage:
    """
    An Storage object is used by partitioner and other components to access
    underlying storage backend without exposing the the implementation details.
    """
    def __init__(self, pywren_config, storage_backend):
        self.pywren_config = pywren_config
        self.backend = storage_backend

        try:
            module_location = 'cloudbutton.engine.storage.backends.{}'.format(self.backend)
            sb_module = importlib.import_module(module_location)
            storage_config = self.pywren_config[self.backend]
            storage_config['user_agent'] = 'cloudbutton/{}'.format(__version__)
            StorageBackend = getattr(sb_module, 'StorageBackend')
            self.storage_handler = StorageBackend(storage_config)
        except Exception as e:
            raise NotImplementedError("An exception was produced trying to create the "
                                      "'{}' storage backend: {}".format(self.backend, e))

    def get_storage_handler(self):
        return self.storage_handler

    def get_client(self):
        client = self.storage_handler.get_client()
        client.put_cobject = self.put_cobject
        client.get_cobject = self.get_cobject
        client.delete_cobject = self.delete_cobject
        client.delete_cobjects = self.delete_cobjects

        return client

    def put_cobject(self, body, bucket=None, key=None):
        """
        Put CloudObject into storage.
        :param body: data content
        :param bucket: destination bucket
        :param key: destination key
        :return: CloudObject instance
        """
        prefix = os.environ.get('CLOUDBUTTON_EXECUTION_ID', '')
        coid = uuid_str().replace('/', '')[:4]
        name = '{}/cloudobject_{}'.format(prefix, coid)
        key = key or '/'.join([TEMP_PREFIX, name])
        bucket = bucket or self.bucket
        self.storage_handler.put_object(bucket, key, body)

        return CloudObject(self.backend, bucket, key)

    def get_cobject(self, cloudobject=None, bucket=None, key=None, stream=False):
        """
        Get CloudObject from storage.
        :param cloudobject: CloudObject instance
        :param bucket: destination bucket
        :param key: destination key
        :return: body text
        """
        if cloudobject:
            if cloudobject.backend == self.backend:
                bucket = cloudobject.bucket
                key = cloudobject.key
                return self.storage_handler.get_object(bucket, key, stream=stream)
            else:
                raise Exception("CloudObject: Invalid Storage backend")
        elif (bucket and key) or key:
            bucket = bucket or self.bucket
            return self.storage_handler.get_object(bucket, key, stream=stream)
        else:
            return None

    def delete_cobject(self, cloudobject=None, bucket=None, key=None):
        """
        Get CloudObject from storage.
        :param cloudobject: CloudObject instance
        :param bucket: destination bucket
        :param key: destination key
        :return: body text
        """
        if cloudobject:
            if cloudobject.backend == self.backend:
                bucket = cloudobject.bucket
                key = cloudobject.key
                return self.storage_handler.delete_object(bucket, key)
            else:
                raise Exception("CloudObject: Invalid Storage backend")
        elif (bucket and key) or key:
            bucket = bucket or self.bucket
            return self.storage_handler.delete_object(bucket, key)
        else:
            return None

    def delete_cobjects(self, cloudobjects):
        """
        Get CloudObject from storage.
        :param cloudobject: CloudObject instance
        :param bucket: destination bucket
        :param key: destination key
        :return: body text
        """
        cobjs = {}
        for co in cloudobjects:
            if co.backend not in cobjs:
                cobjs[co.backend] = {}
            if co.bucket not in cobjs[co.backend]:
                cobjs[co.backend][co.bucket] = []
            cobjs[co.backend][co.bucket].append(co.key)

        for backend in cobjs:
            if backend == self.backend:
                for bucket in cobjs[backend]:
                    self.storage_handler.delete_objects(bucket, cobjs[backend][co.bucket])
            else:
                raise Exception("CloudObject: Invalid Storage backend")


class InternalStorage:
    """
    An InternalStorage object is used by executors and other components to access
    underlying storage backend without exposing the the implementation details.
    """

    def __init__(self, storage_config, executor_id=None):
        self.config = storage_config
        self.backend = self.config['backend']
        self.bucket = self.config['bucket']
        self.executor_id = executor_id

        try:
            module_location = 'cloudbutton.engine.storage.backends.{}'.format(self.backend)
            sb_module = importlib.import_module(module_location)
            StorageBackend = getattr(sb_module, 'StorageBackend')
            self.storage_handler = StorageBackend(self.config[self.backend],
                                                  bucket=self.bucket,
                                                  executor_id=self.executor_id)
        except Exception as e:
            raise NotImplementedError("An exception was produced trying to create the "
                                      "'{}' storage backend: {}".format(self.backend, e))

    def get_storage_config(self):
        """
        Retrieves the configuration of this storage handler.
        :return: storage configuration
        """
        return self.config

    def get_client(self):
        client = self.storage_handler.get_client()
        client.put_cobject = self.put_cobject
        client.get_cobject = self.get_cobject
        client.delete_cobject = self.delete_cobject
        client.delete_cobjects = self.delete_cobjects

        return client

    def put_cobject(self, body, bucket=None, key=None):
        """
        Put CloudObject into storage.
        :param body: data content
        :param bucket: destination bucket
        :param key: destination key
        :return: CloudObject instance
        """
        prefix = os.environ.get('CLOUDBUTTON_EXECUTION_ID', '')
        coid = uuid_str().replace('/', '')[:4]
        name = '{}/cloudobject_{}'.format(prefix, coid)
        key = key or '/'.join([TEMP_PREFIX, name])
        bucket = bucket or self.bucket
        self.storage_handler.put_object(bucket, key, body)

        return CloudObject(self.backend, bucket, key)

    def get_cobject(self, cloudobject=None, bucket=None, key=None, stream=False):
        """
        Get CloudObject from storage.
        :param cloudobject: CloudObject instance
        :param bucket: destination bucket
        :param key: destination key
        :return: body text
        """
        if cloudobject:
            if cloudobject.backend == self.backend:
                bucket = cloudobject.bucket
                key = cloudobject.key
                return self.storage_handler.get_object(bucket, key, stream=stream)
            else:
                raise Exception("CloudObject: Invalid Storage backend")
        elif (bucket and key) or key:
            bucket = bucket or self.bucket
            return self.storage_handler.get_object(bucket, key, stream=stream)
        else:
            return None

    def delete_cobject(self, cloudobject=None, bucket=None, key=None):
        """
        Get CloudObject from storage.
        :param cloudobject: CloudObject instance
        :param bucket: destination bucket
        :param key: destination key
        :return: body text
        """
        if cloudobject:
            if cloudobject.backend == self.backend:
                bucket = cloudobject.bucket
                key = cloudobject.key
                return self.storage_handler.delete_object(bucket, key)
            else:
                raise Exception("CloudObject: Invalid Storage backend")
        elif (bucket and key) or key:
            bucket = bucket or self.bucket
            return self.storage_handler.delete_object(bucket, key)
        else:
            return None

    def delete_cobjects(self, cloudobjects):
        """
        Get CloudObject from storage.
        :param cloudobject: CloudObject instance
        :param bucket: destination bucket
        :param key: destination key
        :return: body text
        """
        cobjs = {}
        for co in cloudobjects:
            if co.backend not in cobjs:
                cobjs[co.backend] = {}
            if co.bucket not in cobjs[co.backend]:
                cobjs[co.backend][co.bucket] = []
            cobjs[co.backend][co.bucket].append(co.key)

        for backend in cobjs:
            if backend == self.backend:
                for bucket in cobjs[backend]:
                    self.storage_handler.delete_objects(bucket, cobjs[backend][co.bucket])
            else:
                raise Exception("CloudObject: Invalid Storage backend")

    def put_data(self, key, data):
        """
        Put data object into storage.
        :param key: data key
        :param data: data content
        :return: None
        """
        return self.storage_handler.put_object(self.bucket, key, data)

    def put_func(self, key, func):
        """
        Put serialized function into storage.
        :param key: function key
        :param func: serialized function
        :return: None
        """
        return self.storage_handler.put_object(self.bucket, key, func)

    def get_data(self, key, stream=False, extra_get_args={}):
        """
        Get data object from storage.
        :param key: data key
        :return: data content
        """
        return self.storage_handler.get_object(self.bucket, key, stream, extra_get_args)

    def get_func(self, key):
        """
        Get serialized function from storage.
        :param key: function key
        :return: serialized function
        """
        return self.storage_handler.get_object(self.bucket, key)

    def get_job_status(self, executor_id, job_id):
        """
        Get the status of a callset.
        :param executor_id: executor's ID
        :return: A list of call IDs that have updated status.
        """
        callset_prefix = '/'.join([JOBS_PREFIX, executor_id, job_id])
        keys = self.storage_handler.list_keys(self.bucket, callset_prefix)

        running_keys = [k[len(JOBS_PREFIX)+1:-len(init_key_suffix)].rsplit("/", 3)
                        for k in keys if init_key_suffix in k]
        running_callids = [((k[0], k[1], k[2]), k[3]) for k in running_keys]

        done_keys = [k for k in keys if status_key_suffix in k]
        done_callids = [tuple(k[len(JOBS_PREFIX)+1:].rsplit("/", 3)[:3]) for k in done_keys]

        return set(running_callids), set(done_callids)

    def get_call_status(self, executor_id, job_id, call_id):
        """
        Get status of a call.
        :param executor_id: executor ID of the call
        :param call_id: call ID of the call
        :return: A dictionary containing call's status, or None if no updated status
        """
        status_key = create_status_key(JOBS_PREFIX, executor_id, job_id, call_id)
        try:
            data = self.storage_handler.get_object(self.bucket, status_key)
            return json.loads(data.decode('ascii'))
        except StorageNoSuchKeyError:
            return None

    def get_call_output(self, executor_id, job_id, call_id):
        """
        Get the output of a call.
        :param executor_id: executor ID of the call
        :param call_id: call ID of the call
        :return: Output of the call.
        """
        output_key = create_output_key(JOBS_PREFIX, executor_id, job_id, call_id)
        try:
            return self.storage_handler.get_object(self.bucket, output_key)
        except StorageNoSuchKeyError:
            return None

    def get_runtime_meta(self, key):
        """
        Get the metadata given a runtime name.
        :param runtime: name of the runtime
        :return: runtime metadata
        """
        path = [RUNTIMES_PREFIX, __version__,  key+".meta.json"]
        filename_local_path = os.path.join(CACHE_DIR, *path)

        if os.path.exists(filename_local_path) and not is_cloudbutton_function():
            logger.debug("Runtime metadata found in local cache")
            with open(filename_local_path, "r") as f:
                runtime_meta = json.loads(f.read())
            return runtime_meta
        else:
            logger.debug("Runtime metadata not found in local cache. Retrieving it from storage")
            try:
                obj_key = '/'.join(path).replace('\\', '/')
                logger.debug('Trying to download runtime metadata from: {}://{}/{}'
                             .format(self.backend, self.bucket, obj_key))
                json_str = self.storage_handler.get_object(self.bucket, obj_key)
                logger.debug('Runtime metadata found in storage')
                runtime_meta = json.loads(json_str.decode("ascii"))
                # Save runtime meta to cache
                if not os.path.exists(os.path.dirname(filename_local_path)):
                    os.makedirs(os.path.dirname(filename_local_path))

                with open(filename_local_path, "w") as f:
                    f.write(json.dumps(runtime_meta))

                return runtime_meta
            except StorageNoSuchKeyError:
                logger.debug('Runtime metadata not found in storage')
                raise Exception('The runtime {} is not installed.'.format(obj_key))

    def put_runtime_meta(self, key, runtime_meta):
        """
        Puit the metadata given a runtime config.
        :param runtime: name of the runtime
        :param runtime_meta metadata
        """
        path = [RUNTIMES_PREFIX, __version__,  key+".meta.json"]
        obj_key = '/'.join(path).replace('\\', '/')
        logger.debug("Uploading runtime metadata to: {}://{}/{}"
                     .format(self.backend, self.bucket, obj_key))
        self.storage_handler.put_object(self.bucket, obj_key, json.dumps(runtime_meta))

        if not is_cloudbutton_function():
            filename_local_path = os.path.join(CACHE_DIR, *path)
            logger.debug("Storing runtime metadata into local cache: {}".format(filename_local_path))

            if not os.path.exists(os.path.dirname(filename_local_path)):
                os.makedirs(os.path.dirname(filename_local_path))

            with open(filename_local_path, "w") as f:
                f.write(json.dumps(runtime_meta))

    def delete_runtime_meta(self, key):
        """
        Puit the metadata given a runtime config.
        :param runtime: name of the runtime
        :param runtime_meta metadata
        """
        path = [RUNTIMES_PREFIX, __version__,  key+".meta.json"]
        obj_key = '/'.join(path).replace('\\', '/')
        filename_local_path = os.path.join(CACHE_DIR, *path)
        if os.path.exists(filename_local_path):
            os.remove(filename_local_path)
        self.storage_handler.delete_object(self.bucket, obj_key)