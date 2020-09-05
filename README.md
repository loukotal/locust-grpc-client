# Locust Grpc client
My try at implementing Grpc client for use with the very nice load testing tool [Locust](https://locust.io/) ([docs](https://docs.locust.io/en/stable/)). This is a very specific implementation that makes some assumptions about rpc request naming. Though if you follow Google's naming conventions, it should be possible to use this out of the box.

Also see [grpc.io docs on how to generated python code from .proto files](https://grpc.io/docs/languages/python/quickstart/#generate-grpc-code).

There is probably a lot of problems how this is implemented, I'll be happy for any feedback / PRs / issues.

## How to use
First setup python environment and install required packages.
1. `python -m virtualenv venv` (or use your favourite flavour of virtualenv)
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`

### A. Setup
#### A.1 Environment variables
1. Fill in required config variables in `locust_grpc.conf`.

    1.1 Default values are  
    - `host` = `localhost`
    - `port` = `3000`
    - `use_secure_channel` = `false`

    1.2. Config Sections
    - separated by `[]`
    - are chosen by `LOCUST_GRPC_ENV` (see 2.1)

2. Set environment variables

    2.1 Used env. vars:
    - `LOCUST_GRPC_CONFIG` - path to the grpc config, default values is `locust_grpc.conf`
    - `LOCUST_GRPC_ENV` - config section from which values from point `1.` will be read. Default value is `local`


#### A.2 Fill in SERVICES variable (in code)
This variable is used for adding `services` and reading generated code by `grpc`. 

Explanation:
```py
SERVICES = {
    "service_name": {
          "stub" : <service_name>_pb2_grpc.<ServiceName>Stub,
          "messages": <service_name>_pb2
      },
}
```
`service_name` can be anything, `stub` and `messages` should stay (otherwise code needs to be modified in `GrpcService`)

Example
```py
from genereated_file import hello_world_pb2_grpc, hello_world_pb2

SERVICES = {
    "hello_world": {
          "stub" : hello_world_pb2_grpc.HelloWorldStub,
          "messages": hello_world_pb2
      },
}
```

#### A.3 Add `GprcServices` to `GrpcClient`
Grpc services should be registered on the `GrpcClient` as such:
```py
class GrpcClient:
    def __init__(self, host, environment, *args, **kwargs):
        self.host = host
        self.hello_world = GrpcService("hello_world", environment)
        # Register more services
```


Note:
> This is a bit clunky, I didn't manage to figure out if there was a better way to use the grpc python implementation for this use case, PRs welcome.

### B. Add Locust code
#### B.1 Tasks
See locust docs on how to implement tasks and add them to the `ApiUser` class.

#### B.2 Use `GrpcClient`
Use the `self.client` attribute to access registered services. Any kwargs passed in to the rpc will be unpacked and used in the request, except for `metadata` kwarg which gets treated separetely. In the example, we are passing in `id=1`

Example:
```py
class ApiUser(GrpcUser):
    @task
    def say_hello(self):
        self.client.hello_world.SayHello(id='1', metadata=[('auth', 'token')])
```

## Problems & TODOs
- [ ] Using custom messages in requests is not tested yet




    



