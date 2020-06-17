# Cloudbutton on vanilla OpenWhisk

Cloudbutton toolkit with *OpenWhisk* as compute backend. Cloudbutton can also run functions on vanilla OpenWhisk installations, for example by deploying OpenWhisk with [openwhisk-devtools](https://github.com/apache/openwhisk-devtools).


### Installation

1. install the [openwhisk-cli](https://github.com/apache/openwhisk-cli)


2. Make sure you can run end-to-end [python example](https://github.com/apache/openwhisk/blob/master/docs/actions-python.md#creating-and-invoking-python-actions).

    For example, create a file named `hello.py` with the next content:
    
    ```python
    def main(args):
        name = args.get("name", "stranger")
        greeting = "Hello " + name + "!"
        print(greeting)
        return {"greeting": greeting}
    ```
    
    Now issue the `wsk` command to deploy the python action:
    
    ```
    $ wsk action create helloPython hello.py
    ```
    
    Finally, test the helloPython action:
    
    ```
    $ wsk action invoke --result helloPython --param name World
    ```

### Configuration

3. Edit your cloudbutton config file and add the following keys:
   ```yaml
    openwhisk:
        endpoint    : <OW_ENDPOINT>
        namespace   : <NAMESPACE>
        api_key     : <AUTH_KEY>
        insecure    : <True/False>
    ```

    - You can find all the values in the `~/.wskprops` file. The content of the file should looks like:

        ```
        APIHOST=192.168.1.30
        AUTH=23bc46b1-71f6-4ed5-8c54-816aa4f8c50:123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCG
        INSECURE_SSL=true
        NAMESPACE=guest
        ```
        
        Copy all the values into the cloudbutton config file as:
        
        ```yaml
        cloudbutton:
            compute_backend: openwhisk
        
        openwhisk:
            endpoint    : https://192.168.1.30
            namespace   : guest
            api_key     : 23bc46b1-71f6-4ed5-8c54-816aa4f8c50:123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCG
            insecure    : True
        ```

#### Summary of configuration keys for Openwhisk:

|Group|Key|Default|Mandatory|Additional info|
|---|---|---|---|---|
|openwhisk | endpoint | |yes | API Host endpoint |
|openwhisk | namespace | |yes | Namespace |
|openwhisk | api_key | |yes | API Auth|
|openwhisk | insecure | |yes | Insecure access |


### Verify

7. Test if Cloudbutton on Openwhisk is working properly:

   Run the next command:
   
   ```bash
   $ cloudbutton test
   ```
   
   or run the next Python code:
   
   ```python
   from cloudbutton.engine.executor import FunctionExecutor
   
   def hello_world(name):
       return 'Hello {}!'.format(name)
    
   if __name__ == '__main__':
        cb_exec = FunctionExecutor()
        cb_exec.call_async(hello_world, 'World')
        print("Response from function: ", cb_exec.get_result())
   ```

