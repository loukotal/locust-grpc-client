import configparser
import os
import time
from functools import partial
from typing import List, Optional

import grpc
from locust import User, task, between

# TODO:
# import generated grpc files
# from v1 import service_pb2, service_pb2_grpc

GRPC_REQUEST_SUFFIX = "Request"

CFG_PATH = os.environ.get("LOCUST_GRPC_CONFIG", "locust_grpc.conf")
TESTING_ENVIRONMENT = os.environ.get("LOCUST_GRPC_ENV", "local")

config = configparser.ConfigParser()
config.read(CFG_PATH)

USE_SECURE_CHANNEL = config.getboolean(TESTING_ENVIRONMENT,"use_secure_channel", fallback=False)
HOST = config.get(TESTING_ENVIRONMENT, "host", fallback="localhost")
PORT = config.get(TESTING_ENVIRONMENT, "port", fallback="3000")

# TODO: Populate SERVICES ie
# { 
#   "service_name": {
#           "stub" : <service_name>_pb2_grpc.<ServiceName>Stub,
#           "messages": <service_name>_pb2
#       },
#   ...
# 
# }
SERVICES = {}

def get_channel(use_secure: bool=False, call_credentials: Optional[List]=None):
    '''
    Helper function - returns a grpc.Channel factory based on 'use_secure' param
    '''
    if use_secure:
        creds = grpc.ssl_channel_credentials()
        if call_credentials is not None:
            creds = grpc.composite_channel_credentials(ssl_creds, *call_credentials)
        return partial(grpc.secure_channel, credentials=creds)
    return grpc.insecure_channel



class GrpcService:

    def __init__(self, service_name, environment, *args, **kwargs):
        self.service = SERVICES[service_name]
        self._locust_environment = environment
        self._grpc_requests = {}

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            grpc_request_name = f"{name}{GRPC_REQUEST_SUFFIX}"
            with  get_channel(USE_SECURE_CHANNEL)(f"{HOST}:{PORT}") as channel:
                # Populate dict with available grpc requests to avoid calling vars _all_ the time
                if self._grpc_requests.get(grpc_request_name, None) is None:
                    self._grpc_requests[grpc_request_name] = vars(self.service["messages"])[grpc_request_name]


                stub = self.service["stub"](channel)
                metadata = kwargs.pop("metadata", None)
                try:
                    result, call = vars(stub)[name].with_call(
                            self._grpc_requests[grpc_request_name](*args, **kwargs),
                            metadata=metadata
                        )
                except Exception as e:
                    total_time = int((time.time() - start_time) * 1000)
                    self._locust_environment.events.request_failure.fire(
                        request_type="grpc", name=name, response_time=total_time, exception=e, response_length=0
                    )
                else:
                    total_time = int((time.time() - start_time) * 1000)
                    self._locust_environment.events.request_success.fire(
                        request_type="grpc", name=name, response_time=total_time, response_length=0
                    )
        return wrapper



class GrpcClient:

    def __init__(self, host, environment, *args, **kwargs):
        self.host = host
        # TODO: Add grpc services
        # ie:
        # self.service = GrpcService(<key_from_SERVICES>, environment)



class GrpcUser(User):
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = GrpcClient(self.host, self.environment)

class ApiUser(GrpcUser):
    host = HOST
    wait_time = between(0.1, 1)

    # TODO: Implement tasks
    # ie:
    # @task
    # def test_name(self):
    #     self.client.service.GetEntity(id='1', metadata=[('authorization', 'Bearer <token>')])