# coding: utf-8
"""
Base para desarrollo de modulos externos.
Para obtener el modulo/Funcion que se esta llamando:
     GetParams("module")

Para obtener las variables enviadas desde formulario/comando Rocketbot:
    var = GetParams(variable)
    Las "variable" se define en forms del archivo package.json

Para modificar la variable de Rocketbot:
    SetVar(Variable_Rocketbot, "dato")

Para obtener una variable de Rocketbot:
    var = GetVar(Variable_Rocketbot)

Para obtener la Opcion seleccionada:
    opcion = GetParams("option")


Para instalar librerias se debe ingresar por terminal a la carpeta "libs"
    
    pip install <package> -t .

"""
from time import sleep
import json
import requests

import shutil
from xml import *
import xml.dom.minidom


class ProcessingSettings:
    Language = "English"
    OutputFormat = "docx"


class Task:
    Status = "Unknown"
    Id = None
    DownloadUrl = None

    def is_active(self):
        if self.Status == "InProgress" or self.Status == "Queued":
            return True
        else:
            return False


class AbbyyOnlineSdk:
    global Task, shutil
    # Warning! This is for easier out-of-the box usage of the sample only. Change to https:// for production use
    # Change to http://cloud-westus.ocrsdk.com if you created your application in US location    
    ServerUrl = "http://cloud-eu.ocrsdk.com/"

    # To create an application and obtain a password,
    # register at https://cloud.ocrsdk.com/Account/Register
    # More info on getting your application id and password at
    # https://ocrsdk.com/documentation/faq/#faq3
    ApplicationId = "user"
    Password = "password"
    Proxies = {}

    def process_image(self, file_path, settings):
        url_params = {
            "language": settings.Language,
            "exportFormat": settings.OutputFormat
        }
        request_url = self.get_request_url("processImage")

        with open(file_path, 'rb') as image_file:
            image_data = image_file.read()

        response = requests.post(request_url, data=image_data, params=url_params,
                                 auth=(self.ApplicationId, self.Password), proxies=self.Proxies)

        # Any response other than HTTP 200 means error - in this case exception will be thrown
        response.raise_for_status()

        # parse response xml and extract task ID
        task = self.decode_response(response.text)
        return task

    def get_task_status(self, task):
        if task.Id.find('00000000-0') != -1:
            # GUID_NULL is being passed. This may be caused by a logical error in the calling code
            print("Null task id passed")
            raise Exception("Null task id passed")
            return None

        url_params = {"taskId": task.Id}
        status_url = self.get_request_url("getTaskStatus")

        response = requests.get(status_url, params=url_params,
                                auth=(self.ApplicationId, self.Password), proxies=self.Proxies)
        task = self.decode_response(response.text)
        return task

    def download_result(self, task, output_path):
        get_result_url = task.DownloadUrl
        if get_result_url is None:
            print("No download URL found")
            raise Exception("No download URL found")
            return

        file_response = requests.get(get_result_url, stream=True, proxies=self.Proxies)
        with open(output_path, 'wb') as output_file:
            shutil.copyfileobj(file_response.raw, output_file)

    def decode_response(self, xml_response):
        """ Decode xml response of the server. Return Task object """
        try:
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml_response)
            task_node = dom.getElementsByTagName("task")[0]
            task = Task()
            task.Id = task_node.getAttribute("id")
            task.Status = task_node.getAttribute("status")
            if task.Status == "Completed":
                task.DownloadUrl = task_node.getAttribute("resultUrl")
        except Exception as e:
            print("error", e)
            print(xml_response)
            raise Exception(e)
        return task

    def get_request_url(self, url):
        return self.ServerUrl.strip('/') + '/' + url.strip('/')


def recognize_file(file_path, result_file_path, language, output_format):
    global ProcessingSettings, processor
    print("Uploading..")
    settings = ProcessingSettings()
    settings.Language = language
    settings.OutputFormat = output_format
    task = processor.process_image(file_path, settings)
    if task is None:
        print("Error")
        return
    if task.Status == "NotEnoughCredits":
        print("Not enough credits to process the document. Please add more pages to your application's account.")
        raise Exception(
            "Not enough credits to process the document. Please add more pages to your application's account.")
        return

    print("Id = {}".format(task.Id))
    print("Status = {}".format(task.Status))

    # Wait for the task to be completed
    print("Waiting..")
    # Note: it's recommended that your application waits at least 2 seconds
    # before making the first getTaskStatus request and also between such requests
    # for the same task. Making requests more often will not improve your
    # application performance.
    # Note: if your application queues several files and waits for them
    # it's recommended that you use listFinishedTasks instead (which is described
    # at https://ocrsdk.com/documentation/apireference/listFinishedTasks/).

    while task.is_active():
        time.sleep(5)
        print(".", end="")
        task = processor.get_task_status(task)

    print("\nStatus = {}".format(task.Status))

    if task.Status == "Completed":
        if task.DownloadUrl is not None:
            processor.download_result(task, result_file_path)
            print("Result was written to {}".format(result_file_path))
    else:
        print("Error processing task")
        raise Exception("Error processing task")


"""
    Obtengo el modulo que fueron invocados
"""
module = GetParams("module")

"""
    Resuelvo catpcha tipo reCaptchav2
"""
processor = None

if module == "GetOCRCloud":
    try:
        File = GetParams("File")
        Pass = GetParams("pass")
        project = GetParams("project")
        url = GetParams("url")
        var_ = GetParams("result")
        processor = AbbyyOnlineSdk()

        data = ""
        processor.ApplicationId = project
        processor.Password = Pass
        processor.ServerUrl = url
        recognize_file(File, "res.txt", "Spanish", "txt")
        with open("res.txt",'r',encoding='utf-8') as f:
            data = f.read()
            f.close()

        try:
            data = data.decode('utf-8')
        except:
            PrintException()
        SetVar(var_, data)
    except Exception as e:
        PrintException()
        raise Exception(e)
