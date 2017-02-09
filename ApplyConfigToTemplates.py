import os.path
import random

from datetime import datetime
from datetime import timedelta
from os import listdir


# Functions Definitions
def read_file_lines(file_name):
    """
    :type file_name: string
    """
    x = open(file_name, 'r')
    final_list = []
    for l in x.readlines()[:]:
        final_list.append(l.strip())
    x.close()
    return final_list


def delete_files_in_dir(directory_name):
    file_list = os.listdir(directory_name)
    for f in file_list[:]:
        os.remove(directory_name + '\\' + f)


def write_list_into_file(file_name, output_list):
    f = open(file_name, 'w')
    i = 0
    j = len(output_list)
    for s in output_list[:]:
        i += 1
        if i < j:
            f.write(s + '\n')
        else:
            f.write(s)
    f.close()


def reg_exp_into_file(file_name, output_list):
    l = len(output_list)
    i = 1
    regular_exp_string = ''
    f = open(file_name, 'w')
    for s in output_list[:]:
        if i < l:
            regular_exp_string += s + '\\r\\n'
        i += 1

    regular_exp_string = "r'" + regular_exp_string + "'"
    f.write(regular_exp_string)
    f.close()


def get_working_days_dict():
    local_dict = {}
    date_index = 0
    for ClaDates in read_file_lines(HomePath + 'CALANDER\\SYSCAL.txt')[:]:
        local_dict[date_index] = ClaDates
        date_index += 1
    return local_dict


def get_config_dict():
    localdict = {}

    global ConfigFileName
    global HomePath

    for varsx in read_file_lines(HomePath + ConfigFileName)[:]:
        if varsx.find("#", 0, len(varsx)) >= 0:
            varsx = varsx.split('#', 1)[0].strip()
        if varsx.startswith('@@_S_'):
            localdict[varsx.split(' ', 1)[0].strip()] = int(varsx.split(' ', 1)[1].strip())
        if varsx.startswith('@@_C_') or varsx.startswith('@@_R_'):
            localdict[varsx.split(' ', 1)[0].strip()] = varsx.split(' ', 1)[1].strip()
        if varsx.startswith('#'):
            pass

    # Sorting in desending order to aviod longer config variables replaced  by shoter length varaibles.
    localdict = dict(sorted(localdict.items(), reverse=True))
    return localdict


def update_sequences_back_to_config_file():
    global ConfigFileName
    global HomePath
    global seqVars
    lines = read_file_lines(HomePath + ConfigFileName)

    output_lines = []
    for line in lines:
        if line.find('@@_R_', 0, len(line)) >= 0 or line.find('@@_S_', 0, len(line)) >= 0:
            for curr_vars in seqVars:
                if curr_vars.startswith("@@_R_") or curr_vars.startswith("@@_S_"):
                    if line.find(curr_vars, 0, len(line)) >= 0:
                        line = line.replace(line.split()[1], str(seqVars[curr_vars]))
        output_lines.append(line)

    os.remove(HomePath + ConfigFileName)
    write_list_into_file(HomePath + ConfigFileName,output_lines)


# This is core
def applychangestotemplate(messagelines, indicator):
    """
    :rtype: String List
    """
    global seqVars, Current_Message_Config_Dict

    if indicator == 'Input':
        localconfig = seqVars
    else:
        localconfig = Current_Message_Config_Dict

    newmessagelines = []
    for nmline in messagelines[:]:
        if nmline.find('@@_', 0, len(nmline)) > 0:
            for VarsL in localconfig:
                if VarsL.startswith('@@_C_'):
                    nmline = nmline.replace(VarsL, localconfig[VarsL])
                if VarsL.startswith('@@_S_'):
                    if nmline.find(VarsL, 0, len(nmline)) > 0:
                        if indicator == 'Input':
                            localconfig[VarsL] = int(localconfig[VarsL]) + 1
                        nmline = nmline.replace(VarsL, str(localconfig[VarsL]))
                if VarsL.startswith('@@_R_'):
                    if nmline.find(VarsL, 0, len(nmline)) > 0:
                        if indicator == 'Input':
                            localconfig[VarsL] = get_next_refrance(localconfig[VarsL])
                        else:
                            pass
                        nmline = nmline.replace(VarsL, str(localconfig[VarsL]))

            # To Add and Business Days from current business Date
            nmline = sub_business_days(addbusinessdays(nmline, 'SYSDATE'), 'SYSDATE')
            # To Add and Sub Calander Days to current business Date
            nmline = subcalanderdays(add_calander_days(nmline, 'SYSDATE'), 'SYSDATE')
            # To Add Months to current business Date         
            nmline = sub_month(add_month(nmline, 'SYSDATE'), 'SYSDATE')

            refdtcounter = 1
            while int(localconfig['@@_C_NOOFREFDATES']) >= refdtcounter:
                ref_date = 'REF' + str(refdtcounter) + '_DATE'
                # To Substract and Add business Days
                nmline = sub_business_days(addbusinessdays(nmline, ref_date), ref_date)
                # To Substract and Add Calander Days
                nmline = subcalanderdays(add_calander_days(nmline, ref_date), ref_date)
                # To Substract and Add Month
                nmline = sub_month(add_month(nmline, ref_date), ref_date)
                refdtcounter += 1
            # To Replace random QTY         
            nmline = applyrandomqty(nmline, 'QTY')

        newmessagelines.append(nmline)
        if 'Input' == indicator:
            seqVars = localconfig

    return newmessagelines


def addbusinessdays(line, refdate):
    return mathbusinessdays(line, refdate, 1)


def sub_business_days(line, refdate):
    return mathbusinessdays(line, refdate, -1)


def applyrandomqty(line, refdate):
    linelen = len(line)
    identifier = '@@_N_' + refdate + '_'

    startchar = line.find(identifier, 0, linelen) + len(identifier)
    if startchar > len(identifier):
        endchar = line.find('X_', startchar, linelen)
        numbertimes = int(line[startchar:endchar])
        repstr = identifier + str(numbertimes) + 'X_'
        newstr = str(CurrRand_Qty * numbertimes)
        line = line.replace(repstr, newstr)
    return line


def mathbusinessdays(line, refdate, add):
    linelen = len(line)
    if add > 0:
        identifier = '@@_D_' + refdate + '_PD'
    else:
        identifier = '@@_D_' + refdate + '_MD'

    startchar = line.find(identifier, 0, linelen) + len(identifier)
    if startchar > len(identifier):
        endchar = line.find('_', startchar, linelen)
        numberdays = int(line[startchar:endchar])
        repstr = identifier + str(numberdays) + '_'
        newstr = get_next_business_date(seqVars['@@_C_' + refdate], add * numberdays)
        line = line.replace(repstr, newstr)
    return line


def add_calander_days(line, refdate):
    return mathcalanderdays(line, refdate, 1)


def subcalanderdays(line, refdate):
    return mathcalanderdays(line, refdate, -1)


def mathcalanderdays(line, reference_date, add):
    linelen = len(line)
    if add > 0:
        identifier = '@@_D_' + reference_date + '_AD'
    else:
        identifier = '@@_D_' + reference_date + '_SD'

    startchar = line.find(identifier, 0, linelen) + len(identifier)
    if startchar > len(identifier):
        last_char = line.find('_', startchar, linelen)
        number_of_days = int(line[startchar:last_char])
        repstr = identifier + str(number_of_days) + '_'

        ref_year = seqVars['@@_C_' + reference_date][0:4]
        ref_month = seqVars['@@_C_' + reference_date][4:6]
        ref_day = seqVars['@@_C_' + reference_date][6:8]

        date1 = datetime.strptime(ref_year + '/' + ref_month + '/' + ref_day, '%Y/%m/%d')
        date1 = date1 + timedelta(days=add * number_of_days)
        newstr = str(date1.year) + str(date1.month).rjust(2, '0') + str(date1.day).rjust(2, '0')
        line = line.replace(repstr, newstr)
    return line


def add_month(line, refdate):
    return mathmonths(line, refdate, 1)


def sub_month(line, ref_date):
    return mathmonths(line, ref_date, -1)


def mathmonths(line, ref_date, add):
    length_of_line = len(line)
    if add > 0:
        identifier = '@@_D_' + ref_date + '_AM'
    else:
        identifier = '@@_D_' + ref_date + '_SM'

    reference_date = seqVars['@@_C_' + ref_date]

    reference_year = reference_date[0:4]
    reference_month = reference_date[4:6]
    reference_day = reference_date[6:8]

    startchar = line.find(identifier, 0, length_of_line) + len(identifier)
    if startchar > len(identifier):
        end_char = line.find('_', startchar, length_of_line)
        number_of_months = int(line[startchar:end_char])
        repstr = identifier + str(number_of_months) + '_'

        if add > 0:
            newyear = int(int(number_of_months) / 12) + int(reference_year)
            newmonth = int(reference_month) + number_of_months % 12

            if newmonth > 12:
                newmonth %= 12
                newyear += 1
        else:
            newyear = int(reference_year) - int(number_of_months / 12)
            newmonth = int(reference_month) - number_of_months % 12
            if newmonth <= 0:
                newmonth += 12
                newyear -= 1
        newstr = adjustdaymonth(newyear, newmonth, int(reference_day))
        line = line.replace(repstr, newstr)
    return line


def adjustdaymonth(year, month, day):
    last_day_of_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    leaplastday = last_day_of_month
    leaplastday[2] = 29

    if year % 4 == 0:
        if day > leaplastday[month]:
            day = leaplastday[month]
    else:
        if day > last_day_of_month[month]:
            day = last_day_of_month[month]

    return str(year) + str(month).rjust(2, '0') + str(day).rjust(2, '0')


def get_next_refrance(inputref):
    length = len(inputref)
    # Input  = upper(Input)
    output = ''
    nextcharchangerequired = True
    while nextcharchangerequired and length > 0:
        length -= 1
        currentchar = inputref[length:length + 1]
        if currentchar == '9':
            nextcharchangerequired = True
            output = output + getnextchar(currentchar)
        else:
            output = inputref[0:length] + getnextchar(currentchar) + output
            length = 0
    return output


def getnextchar(onechar):
    # OneChar = upper(OneChar)
    alphanumstrupple = ('A', 'B', 'C', 'D', 'E', 'F', 'G',
                        'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
                        'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
                        'Z', '0', '1', '2', '3', '4', '5', '6', '7',
                        '8', '9')

    if onechar == '9':
        return 'A'

    location = 0
    for X in alphanumstrupple:
        location += 1
        if X == onechar:
            return alphanumstrupple[location]
    return 'A'


def get_next_business_date(input_date, number_of_days):
    i = 0
    while WorkingDayDict[i] != input_date:
        i += 1
    return WorkingDayDict[i + number_of_days]


def getcurrentdayindex(indate):
    i = 0
    while WorkingDayDict[i] != indate:
        i += 1
    return i


# Main-Process-Start Here
HomePath = 'C:\\PYTON\\BIS_TEST_MESSAGES\\'
ConfigFileName = 'CONFIG\\MasterInfo_1.txt'
# Getting working days Dates:
WorkingDayDict = get_working_days_dict()
# Configuration Variables to dictionary
seqVars = get_config_dict()
Current_Message_Config_Dict = {}

CurrBusiDayIndex = getcurrentdayindex(seqVars['@@_C_SYSDATE'])
CurrRand_Qty = random.randrange(1, 200, 1)

delete_files_in_dir(HomePath + 'OUTPUTMSGS')

for Folder in next(os.walk(HomePath + '\\TEMPLATES'))[1]:
    os.makedirs(HomePath + '\\OUTPUTMSGSR\\' + Folder, 777, True)
    for txtFile in listdir(HomePath + '\\TEMPLATES\\' + Folder)[:]:
        MessageTemplate = HomePath + '\\TEMPLATES\\' + Folder + '\\' + txtFile
        OutPutFile = HomePath + '\\OUTPUTMSGS\\' + Folder + '_' + txtFile
        print(txtFile)
        write_list_into_file(OutPutFile, applychangestotemplate(read_file_lines(MessageTemplate), "Input"))
        Current_Message_Config_Dict = seqVars
        txtFile = txtFile.split('.')[0].strip()
        os.makedirs(HomePath + '\\OUTPUTMSGSR\\' + Folder + '\\' + txtFile, 777, True)
        # Static Configuration Variables applied for the file.
        txtFile = txtFile.split('.')[0].strip()
        if os.path.isdir(HomePath + '\\REASULTS\\' + Folder + '\\' + txtFile):
            for ReasultTemplates in listdir(HomePath + '\\REASULTS\\' + Folder + '\\' + txtFile)[:]:
                OutPutFolder = HomePath + '\\OUTPUTMSGSR\\' + Folder + '\\' + txtFile
                OutPutFile = OutPutFolder + '\\' + ReasultTemplates
                XX = HomePath + '\\REASULTS\\' + Folder + '\\' + txtFile + '\\' + ReasultTemplates
                reg_exp_into_file(OutPutFile, applychangestotemplate(read_file_lines(XX), "Reasult"))
update_sequences_back_to_config_file()
