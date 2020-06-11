import os
import io
import shutil
import logging
from cloudbutton.engine.backends.storage.utils import StorageNoSuchKeyError
from cloudbutton.config import STORAGE_FOLDER


logger = logging.getLogger(__name__)


class LocalhostStorageBackend:
    """
    A wrap-up around Localhost filesystem APIs.
    """

    def __init__(self, config, **kwargs):
        logger.debug("Creating Localhost storage client")
        self.config = config
        logger.debug("Localhost storage client created successfully")

    def get_client(self):
        # Simulate boto3 client
        class LocalhostBoto3Client():
            def __init__(self, backend):
                self.backend = backend

            def put_object(self, Bucket, Key, Body, **kwargs):
                self.backend.put_object(Bucket, Key, Body)

            def get_object(self, Bucket, Key, **kwargs):
                body = self.backend.get_object(Bucket, Key, stream=True, extra_get_args=kwargs)
                return {'Body': body}

            def list_objects(self, Bucket, Prefix=None, **kwargs):
                return self.backend.list_objects(Bucket, Prefix)

            def list_objects_v2(self, Bucket, Prefix=None, **kwargs):
                return self.backend.list_objects(Bucket, Prefix)

        return LocalhostBoto3Client(self)

    def put_object(self, bucket_name, key, data):
        """
        Put an object in localhost filesystem.
        Override the object if the key already exists.
        :param key: key of the object.
        :param data: data of the object
        :type data: str/bytes
        :return: None
        """
        try:
            data_type = type(data)
            file_path = os.path.join(STORAGE_FOLDER, bucket_name, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if data_type == bytes:
                with open(file_path, "wb") as f:
                    f.write(data)
            else:
                with open(file_path, "w") as f:
                    f.write(data)
        except Exception as e:
            raise(e)

    def get_object(self, bucket_name, key, stream=False, extra_get_args={}):
        """
        Get object from localhost filesystem with a key.
        Throws StorageNoSuchKeyError if the given key does not exist.
        :param key: key of the object
        :return: Data of the object
        :rtype: str/bytes
        """
        buffer = None
        try:
            file_path = os.path.join(STORAGE_FOLDER, bucket_name, key)
            with open(file_path, "rb") as f:
                if 'Range' in extra_get_args:
                    byte_range = extra_get_args['Range'].replace('bytes=', '')
                    first_byte, last_byte = map(int, byte_range.split('-'))
                    f.seek(first_byte)
                    buffer = io.BytesIO(f.read(last_byte-first_byte+1))
                else:
                    buffer = io.BytesIO(f.read())
            if stream:
                return buffer
            else:
                return buffer.read()
        except Exception:
            raise StorageNoSuchKeyError(os.path.join(STORAGE_FOLDER, bucket_name), key)

    def head_object(self, bucket_name, key):
        """
        Head object from local filesystem with a key.
        Throws StorageNoSuchKeyError if the given key does not exist.
        :param key: key of the object
        :return: Data of the object
        :rtype: str/bytes
        """
        pass

    def delete_object(self, bucket_name, key):
        """
        Delete an object from storage.
        :param bucket: bucket name
        :param key: data key
        """
        file_path = os.path.join(STORAGE_FOLDER, bucket_name, key)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    def delete_objects(self, bucket_name, key_list):
        """
        Delete a list of objects from storage.
        :param bucket: bucket name
        :param key_list: list of keys
        """
        dirs = set()
        for key in key_list:
            file_dir = os.path.dirname(key)
            dirs.add(file_dir)
            # dirs.add("/".join(file_dir.split("/", 2)[:2]))
            self.delete_object(bucket_name, key)

        for file_dir in dirs:
            shutil.rmtree(os.path.join(STORAGE_FOLDER, file_dir), ignore_errors=True)

    def bucket_exists(self, bucket_name):
        """
        Head localhost dir with a name.
        Throws StorageNoSuchKeyError if the given bucket does not exist.
        :param bucket_name: name of the bucket
        """
        raise NotImplementedError

    def head_bucket(self, bucket_name):
        """
        Head localhost dir with a name.
        Throws StorageNoSuchKeyError if the given bucket does not exist.
        :param bucket_name: name of the bucket
        :return: Metadata of the bucket
        :rtype: str/bytes
        """
        raise NotImplementedError

    def list_objects(self, bucket_name, prefix=None):
        """
        Return a list of objects for the prefix.
        :param bucket_name: Name of the bucket.
        :param prefix: Prefix to filter object names.
        :return: List of objects in bucket that match the given prefix.
        :rtype: list of str
        """
        key_list = []

        if prefix:
            root = os.path.join(STORAGE_FOLDER, bucket_name, prefix)
        else:
            root = os.path.join(STORAGE_FOLDER, bucket_name)

        for path, subdirs, files in os.walk(root):
            for name in files:
                size = os.stat(os.path.join(path, name)).st_size
                if prefix:
                    key_list.append({'Key': os.path.join(prefix, path.replace(root+'/', ''), name), 'Size': size})
                else:
                    key_list.append({'Key': os.path.join(path.replace(root+'/', ''), name), 'Size': size})

        return key_list

    def list_keys(self, bucket_name, prefix=None):
        """
        Return a list of keys for the given prefix.
        :param bucket_name: Name of the bucket.
        :param prefix: Prefix to filter object names.
        :return: List of keys in bucket that match the given prefix.
        :rtype: list of str
        """
        key_list = []

        if prefix:
            root = os.path.join(STORAGE_FOLDER, bucket_name, prefix)
        else:
            root = os.path.join(STORAGE_FOLDER, bucket_name)

        for path, subdirs, files in os.walk(root):
            for name in files:
                if prefix:
                    key_list.append(os.path.join(prefix, path.replace(root+'/', ''), name))
                else:
                    key_list.append(os.path.join(path.replace(root+'/', ''), name))

        return key_list