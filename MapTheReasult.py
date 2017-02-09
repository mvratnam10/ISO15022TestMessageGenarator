import os.path
from os import listdir
import re


# Functions Definitions
def read_file_lines(file_name):
    local_file_obj = open(file_name, 'r')
    file_content = local_file_obj.read()
    local_file_obj.close()
    return file_content


def write_into_file(file_name, file_content):
    f =open(file_name, 'w')
    f.write(file_content)
    f.close()


def getvars(inputstr,type):
    x=''
    local_config={}
    if type == '_K001.txt':
        x=re.findall(r':70D::REAS///CPSAFREF/ZA\d{6}/\d{7}',inputstr)[0]
        local_config =+ {'@@_V_REC_ORD_NO':x}
        x=str(int(x)-1).rjust(7,'0')
        local_config = + {'@@_V_DEL_ORD_NO':x}
    return local_config

def applychangestotemplate(messagelines):
    global ConfigVars
    localconfig=ConfigVars
    for vars in localconfig:
        messagelines=messagelines.replace(vars, localconfig[vars])
    return messagelines


# Main-Process-Start Here
HomePath = 'C:\\PYTON\\BIS_TEST_MESSAGES\\OUTPUTMSGSR'
OutPutPath='C:\\PYTON\\BIS_TEST_MESSAGES\\OUTMSG'
# Configuration Variables to dictionary
ConfigVars={}
print("Started")
for Module in next(os.walk(HomePath))[1]:
    CurrentPath=HomePath+'\\'+Module
    for InPutMessage in next(os.walk(CurrentPath))[1]:
        CurrentPath = HomePath+'\\'+Module+'\\' + InPutMessage
        MatchFound = False
        for ExpectedResult in listdir(CurrentPath)[:]:
            ReasultPath = CurrentPath
            CurrentPath= ReasultPath + '\\' + ExpectedResult
            exp = applychangestotemplate(read_file_lines(CurrentPath))
            file_name_suffix = re.findall('\B_k\d\d\d.txt', ExpectedResult)[0]
            for OutPutMsg in listdir(OutPutPath)[:]:
                TestRslt = read_file_lines(OutPutPath+'\\'+ OutPutMsg)
                x=re.match(exp,TestRslt)
                if x!=None:
                    if x.span()[1] > 0:
                        MatchFound = True
                        if os._exists(ReasultPath)!=True:
                            os.makedirs(ReasultPath, 777, True)
                        write_into_file(ReasultPath + '\\' + ExpectedResult, TestRslt)
                        if file_name_suffix.startswith('_K'):
                            ConfigVars = getvars(TestRslt,file_name_suffix)
                        os.remove(OutPutPath+'\\'+ OutPutMsg)
                        break

            if MatchFound==False:
                print("No Match for "+ CurrentPath)