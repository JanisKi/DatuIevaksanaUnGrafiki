import paramiko
import time
import pandas as pd
from collections import defaultdict
import psycopg2
import config
import datetime
from datetime import datetime

def open_ssh(serverIP,username):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(serverIP, username=username,password='deac2022')
    return client

def execute_load(client,slodze,laiks):
    command='stress-ng -c 0 -l {} -t {}s'.format(slodze,int(laiks)*60)
    session=client.get_transport().open_session()
    session.exec_command(command)
    return

def read_temp(client):
    session=client.get_transport().open_session()
    session.exec_command('sensors')
    return (session.recv(1024)[54:58]).decode('utf-8')

def close_ssh(client):
    client.close()
    return

def vienslists(lst):
    onelist=[]
    for x in lst:
        for i in x:
            onelist.append(i)
    return onelist


# No masīva iegūst vidējo temperatūru
def avgtemp(lst):
    x=len(lst)
    b=0
    for tmp in lst:
        b=b+float(tmp)
    return b/x


# Šķiro dictionary masīvus
# Netiek izmantots
def testins(alists,tlist,otrslists,b=1):
    my_dict={}
    my_dict["ID"]=alists[b]
    for i in range(len(otrslists)):
        my_dict[otrslists[i]]=tlist[b]
    return my_dict


# Izveido savienojumu ar datu bāzi
def get_connection():
    connection = psycopg2.connect(user="rtu170",
                                  password="deac2022",
                                  host="192.168.99.165",
                                  port="5432",
                                  database="ExDatiDB")
    return connection


# Aizver savienojumu ar datu bāzi
# Netiek izmantots
def close_connection(connection):
    if connection:
        connection.close()



"""
      Var izveidot kā vienu funkciju, lai iegūtu ID/IP/USER
"""


# Iegūst no konkrētā skapja serveru ID
def read_database_id(skapis):
    idLst=[]
    try:
        connection = get_connection()
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from exdati"
        cursor.execute(postgreSQL_select_Query)
        exdatidb = cursor.fetchall()

        for row in exdatidb:
            if row[1] == skapis:
                idLst.append(row[0])
        close_connection(connection)
    except (Exception, psycopg2.Error) as error:
        print("Error while getting data", error)

    return idLst


# Iegūst no konkrētā skapja serveru IP
def read_database_ip(skapis):
    ipLst=[]
    try:
        connection = get_connection()
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from exdati"
        cursor.execute(postgreSQL_select_Query)
        exdatidb = cursor.fetchall()

        for row in exdatidb:
            if row[1] == skapis:
                ipLst.append(row[2])
        close_connection(connection)
    except (Exception, psycopg2.Error) as error:
        print("Error while getting data", error)

    return ipLst


# Iegūst no konkrētā skapja serveru UserName
def read_database_user(skapis):
    userLst=[]
    try:
        connection = get_connection()
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from exdati"
        cursor.execute(postgreSQL_select_Query)
        exdatidb = cursor.fetchall()

        for row in exdatidb:
            if row[1] == skapis:
                userLst.append(row[3])
        close_connection(connection)
    except (Exception, psycopg2.Error) as error:
        print("Error while getting data", error)

    return userLst


# Nolasa datus no datubāzes ( Testu Grafika )
# Kā ari atrod neuzsāktos testus
# Izvada visu priekš neuzsāktā testa
def read_database_testinfo():
    aktivitate=[]
    testdate=[]
    tuvakaisdatums=''
    skapji=''
    datums=''
    laiks=''
    slodze=''
    try:
        connection = get_connection()
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from TestuGrafiks"
        cursor.execute(postgreSQL_select_Query)
        exdatidb = cursor.fetchall()

        for row in exdatidb: 
            aktivitate=row[5]
            if aktivitate == 'neaktivs':
                testdate.append(row[2])
                for date in testdate:
                    if tuvakaisdatums > date or tuvakaisdatums == '':
                        tuvakaisdatums = date
                        grafiksid=row[0]
                        skapji=row[1]
                        datums=row[2]
                        laiks=row[3]
                        slodze=row[4]
                    else:
                        grafiksid='003249d6-b520-4191-a623-21fc77c04344'
                        skapji='1'
                        datums='20-12-2022 08:00:00'
                        laiks=10
                        slodze=25

        close_connection(connection)

    except (Exception, psycopg2.Error) as error:
        print("Error while getting data", error)
    #print('asd')
    return grafiksid,skapji,datums,laiks,slodze   


# Ievieto datubāzē veikto testu katram serverim
# Pēc serveru ID, Temperaturas, Slodzes
def insert_database(con,serverid,temp,slodze):
    try:
        connection=con
        cursor = connection.cursor()  # Insert into "Tabale Name (kolonna,kolonna,kolonna)"
        postgres_insert_query = """ INSERT INTO exp (servertestid, temperature, slodze) VALUES (%s,%s,%s)""" 
        record_to_insert = (serverid, temp, slodze) 
        cursor.execute(postgres_insert_query, record_to_insert)

        connection.commit()
        count = cursor.rowcount
        #print(count, "Record inserted successfully into exp table")

    except(Exception, psycopg2.Error) as error:
            print("Failed to insert record into exp table", error)

    finally:
        return


# Ja ir uzsākts tests, tad tests tiek atjauninats
# Datubāzēs norādot - aktīvs/pabeigts
def update_testugrafiks(grafiksid, aktivitate):
    sql = """
          UPDATE testugrafiks
          SET aktivitate = %s
          WHERE grafiksid = %s
          """
    try:
        connection = get_connection() 
        cursor = connection.cursor()
        cursor.execute(sql, (aktivitate, grafiksid))
        
        connection.commit()
        count = cursor.rowcount
        print(count, "Record inserted successfully into exp table")
    except(Exception, psycopg2.Error) as error:
            print("Failed to insert record into testugrafiks table", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")            

while True:
    skapji=''
    datums=''
    laiks=''
    slodz=''
    serveruID=[]
    adreses=[]
    username=[]

    skapis1='8d674cc5-56be-40db-a51c-5db5ca2555ad'
    skapis2='42032aad-deee-45a3-a4a7-40a3c9336a74'
    skapis3='28e52f26-80c7-41bb-aa5b-33c81c9df88c'

    # Nolasa no Testu grafika - Grafika ID, Skapjus, kuriem jāveic testi, datumu, laiku, slodzi
    grafiksId,skapji,datums,laiks,slodz=read_database_testinfo()
    
    CurrentDate = str(datetime.now())[0:16]
    ExpectedDate = datums#datetime.strptime(datums, "%d-%m-%Y %H:%M:%S")
    ExpectedDateFiveBehind=str(ExpectedDate)[0:16]
    ExpectedDateFiveInfront=str(ExpectedDate)[0:16]

    # Tā kā datu bāzēs laiks tika pierakstīts MM-DD-YYYY
    # Un Pythonā laiks tiek dots DD-MM-YYYY
    # Izveidoju vienkāršāku veidu, kas atļauj veikt testu 5min pirms vai pēc testa veikšanas laika
    if ExpectedDateFiveBehind[14:16] == '00':
        testvarhour=ExpectedDateFiveBehind[11:13]
        testvarmin=ExpectedDateFiveBehind[14:16]
        if testvarhour == '00':
            testvarhour='23'
        testvarmin='55'
        ExpectedDateFiveBehind=ExpectedDateFiveBehind[:10]+' '+testvarhour
        ExpectedDateFiveBehind=ExpectedDateFiveBehind+':' +testvarmin
    elif 60-int(ExpectedDateFiveBehind[14:16]) >= 55:
        testvarhour=ExpectedDateFiveBehind[11:13]
        testvarmin=ExpectedDateFiveBehind[14:16]
        if testvarmin == '05':
            testvarmin='00'
        elif testvarmin == '04':
            testvarmin='59'
        elif testvarmin == '03':
            testvarmin='58'
        elif testvarmin == '02':
            testvarmin='57'
        elif testvarmin == '01':
            testvarmin='56'
        if testvarhour == '00':
            testvarhour='23'  
        else:
            if len(str(int(testvarhour)-1))<=1:
                testvarhour='0'+str(int(testvarhour)-1)
            else:
                testvarhour=str(int(testvarhour)-1)
        ExpectedDateFiveBehind=ExpectedDateFiveBehind[:10]+' '+testvarhour
        ExpectedDateFiveBehind=ExpectedDateFiveBehind+':' +testvarmin
    else:
        testvarhour=ExpectedDateFiveBehind[11:13]
        testvarmin=ExpectedDateFiveBehind[14:16]
        if len(str(int(testvarmin)-5))<=1:
            testvarmin='0'+str(int(testvarmin)-5)
        else:
            testvarmin=str(int(testvarmin)-5)
        ExpectedDateFiveBehind=ExpectedDateFiveBehind[:10]+' '+testvarhour
        ExpectedDateFiveBehind=ExpectedDateFiveBehind+':' +testvarmin

    if ExpectedDateFiveInfront[14:16] == '00':
        testvarhour=ExpectedDateFiveInfront[11:13]
        testvarmin=ExpectedDateFiveInfront[14:16]
        if testvarhour == '00':
            testvarhour='01'
        testvarmin='05'
        ExpectedDateFiveInfront=ExpectedDateFiveInfront[:10]+' '+testvarhour
        ExpectedDateFiveInfront=ExpectedDateFiveInfront+':' +testvarmin
    elif 60-int(ExpectedDateFiveInfront[14:16]) <= 5:
        testvarhour=ExpectedDateFiveInfront[11:13]
        testvarmin=ExpectedDateFiveInfront[14:16]
        if testvarhour == '00':
            testvarhour='01'
        if testvarmin == '55':
            testvarmin='00'
        elif testvarmin == '56':
            testvarmin='01'
        elif testvarmin == '57':
            testvarmin='02'
        elif testvarmin == '58':
            testvarmin='03'
        elif testvarmin == '59':
            testvarmin='04'
        if testvarhour == '00':
            testvarhour='01'
        else:
            if len(str(int(testvarhour)+1))<=1:
                testvarhour='0'+str(int(testvarhour)+1)
            else:
                testvarhour=str(int(testvarhour)+1)
        ExpectedDateFiveInfront=ExpectedDateFiveInfront[:10]+' '+testvarhour
        ExpectedDateFiveInfront=ExpectedDateFiveInfront+':' +testvarmin
    else:
        testvarhour=ExpectedDateFiveInfront[11:13]
        testvarmin=ExpectedDateFiveInfront[14:16]
        if len(str(int(testvarmin)+5))<=1:
            testvarmin='0'+str(int(testvarmin)+5)
        else:
            testvarmin=str(int(testvarmin)+5)
        ExpectedDateFiveInfront=ExpectedDateFiveInfront[:10]+' '+testvarhour
        ExpectedDateFiveInfront=ExpectedDateFiveInfront+':' +testvarmin
        
    ExpectedDateinfront1 = datetime.strptime(ExpectedDateFiveInfront[0:16], "%d-%m-%Y %H:%M")
    ExpectedDatebehind1 = datetime.strptime(ExpectedDateFiveBehind[0:16], "%d-%m-%Y %H:%M")

    # Tiek pārbaudīts vai tests ir tuvāko 5 min., laikā
    # Ja tas ir, tad tiek pārbaudīts, kuriem serveru skapjiem tiek veikti testi
    # Kā arī iegūts serveru skapju info.

    #print(ExpectedDatebehind1)
    #print(ExpectedDateinfront1)

    
    # Atcels testus, kas nav savlaicigi veikti
    # Ja testu nav paspets veikt, tad tas tiek atcelts
    """
    elif str(ExpectedDatebehind1)>= ExpectedDate: 
        update_testugrafiks(grafiksId, 'atcelts')
    
    """
    
    if str(ExpectedDateinfront1) >= CurrentDate and CurrentDate >= str(ExpectedDatebehind1):
        update_testugrafiks(grafiksId,'aktīvs')
        if '1' in skapji:
            serveruID.append(read_database_id(skapis1))
            adreses.append(read_database_ip(skapis1))
            username.append(read_database_user(skapis1))
        if '2' in skapji:
            serveruID.append(read_database_id(skapis2))
            adreses.append(read_database_ip(skapis2))
            username.append(read_database_user(skapis2))
        if '3' in skapji:
            serveruID.append(read_database_id(skapis3))
            adreses.append(read_database_ip(skapis3))
            username.append(read_database_user(skapis3))
        if 'All' in skapji:
            serveruID.append(read_database_id(skapis1))
            adreses.append(read_database_ip(skapis1))
            username.append(read_database_user(skapis1))
            serveruID.append(read_database_id(skapis2))
            adreses.append(read_database_ip(skapis2))
            username.append(read_database_user(skapis2))
            serveruID.append(read_database_id(skapis3))
            adreses.append(read_database_ip(skapis3))
            username.append(read_database_user(skapis3))


        print("Tiks uzsākti testi - {} serveriem, ar slodzi - {}% un laika periodā - {}".format(skapji,slodz,laiks))

        serveruID=vienslists(serveruID)
        ip=vienslists(adreses)
        user=vienslists(username)

        time_start1= time.time()
        server0 = open_ssh("{}".format(ip[0]),"{}".format(user[0]))
        server1 = open_ssh("{}".format(ip[1]),"{}".format(user[1]))
        server2 = open_ssh("{}".format(ip[2]),"{}".format(user[2]))
        server3 = open_ssh("{}".format(ip[3]),"{}".format(user[3]))
        server4 = open_ssh("{}".format(ip[4]),"{}".format(user[4]))
        server5 = open_ssh("{}".format(ip[5]),"{}".format(user[5]))
        server6 = open_ssh("{}".format(ip[6]),"{}".format(user[6]))
        server7 = open_ssh("{}".format(ip[7]),"{}".format(user[7]))
        server8 = open_ssh("{}".format(ip[8]),"{}".format(user[8]))
        server9 = open_ssh("{}".format(ip[9]),"{}".format(user[9]))
        server10 = open_ssh("{}".format(ip[10]),"{}".format(user[10]))
        server11 = open_ssh("{}".format(ip[11]),"{}".format(user[11]))
        server12 = open_ssh("{}".format(ip[12]),"{}".format(user[12]))
        server13 = open_ssh("{}".format(ip[13]),"{}".format(user[13]))
        server14 = open_ssh("{}".format(ip[14]),"{}".format(user[14]))
        server15 = open_ssh("{}".format(ip[15]),"{}".format(user[15]))
        server16 = open_ssh("{}".format(ip[16]),"{}".format(user[16]))
        server17 = open_ssh("{}".format(ip[17]),"{}".format(user[17]))
        server18 = open_ssh("{}".format(ip[18]),"{}".format(user[18]))
        server19 = open_ssh("{}".format(ip[19]),"{}".format(user[19]))
        server20 = open_ssh("{}".format(ip[20]),"{}".format(user[20]))
        server21 = open_ssh("{}".format(ip[21]),"{}".format(user[21]))
        server22 = open_ssh("{}".format(ip[22]),"{}".format(user[22]))
        server23 = open_ssh("{}".format(ip[23]),"{}".format(user[23]))
        server24 = open_ssh("{}".format(ip[24]),"{}".format(user[24]))
        server25 = open_ssh("{}".format(ip[25]),"{}".format(user[25]))
        server26 = open_ssh("{}".format(ip[26]),"{}".format(user[26]))
        server27 = open_ssh("{}".format(ip[27]),"{}".format(user[27]))
        server28 = open_ssh("{}".format(ip[28]),"{}".format(user[28]))
        server29 = open_ssh("{}".format(ip[29]),"{}".format(user[29]))
        server30 = open_ssh("{}".format(ip[30]),"{}".format(user[30]))
        server31 = open_ssh("{}".format(ip[31]),"{}".format(user[31]))
        server32 = open_ssh("{}".format(ip[32]),"{}".format(user[32]))
        server33 = open_ssh("{}".format(ip[33]),"{}".format(user[33]))
        server34 = open_ssh("{}".format(ip[34]),"{}".format(user[34]))
        server35 = open_ssh("{}".format(ip[35]),"{}".format(user[35]))
        server36 = open_ssh("{}".format(ip[36]),"{}".format(user[36]))
        server37 = open_ssh("{}".format(ip[37]),"{}".format(user[37]))
        server38 = open_ssh("{}".format(ip[38]),"{}".format(user[38]))
        server39 = open_ssh("{}".format(ip[39]),"{}".format(user[39]))
        server40 = open_ssh("{}".format(ip[40]),"{}".format(user[40]))
        server41 = open_ssh("{}".format(ip[41]),"{}".format(user[41]))
        server42 = open_ssh("{}".format(ip[42]),"{}".format(user[42]))
        server43 = open_ssh("{}".format(ip[43]),"{}".format(user[43]))
        server44 = open_ssh("{}".format(ip[44]),"{}".format(user[44]))
        server45 = open_ssh("{}".format(ip[45]),"{}".format(user[45]))
        server46 = open_ssh("{}".format(ip[46]),"{}".format(user[46]))
        server47 = open_ssh("{}".format(ip[47]),"{}".format(user[47]))
        server48 = open_ssh("{}".format(ip[48]),"{}".format(user[48]))
        server49 = open_ssh("{}".format(ip[49]),"{}".format(user[49]))
        server50 = open_ssh("{}".format(ip[50]),"{}".format(user[50]))
        server51 = open_ssh("{}".format(ip[51]),"{}".format(user[51]))
        server52 = open_ssh("{}".format(ip[52]),"{}".format(user[52]))
        server53 = open_ssh("{}".format(ip[53]),"{}".format(user[53]))
        server54 = open_ssh("{}".format(ip[54]),"{}".format(user[54]))
        server55 = open_ssh("{}".format(ip[55]),"{}".format(user[55]))
        server56 = open_ssh("{}".format(ip[56]),"{}".format(user[56]))
        server57 = open_ssh("{}".format(ip[57]),"{}".format(user[57]))
        server58 = open_ssh("{}".format(ip[58]),"{}".format(user[58]))
        server59 = open_ssh("{}".format(ip[59]),"{}".format(user[59]))
        server60 = open_ssh("{}".format(ip[60]),"{}".format(user[60]))
        server61 = open_ssh("{}".format(ip[61]),"{}".format(user[61]))
        server62 = open_ssh("{}".format(ip[62]),"{}".format(user[62]))
        server63 = open_ssh("{}".format(ip[63]),"{}".format(user[63]))
        server64 = open_ssh("{}".format(ip[64]),"{}".format(user[64]))
        server65 = open_ssh("{}".format(ip[65]),"{}".format(user[65]))
        server66 = open_ssh("{}".format(ip[66]),"{}".format(user[66]))
        server67 = open_ssh("{}".format(ip[67]),"{}".format(user[67]))
        server68 = open_ssh("{}".format(ip[68]),"{}".format(user[68]))
        server69 = open_ssh("{}".format(ip[69]),"{}".format(user[69]))
        server70 = open_ssh("{}".format(ip[70]),"{}".format(user[70]))
        server71 = open_ssh("{}".format(ip[71]),"{}".format(user[71]))
        server72 = open_ssh("{}".format(ip[72]),"{}".format(user[72]))
        server73 = open_ssh("{}".format(ip[73]),"{}".format(user[73]))
        server74 = open_ssh("{}".format(ip[74]),"{}".format(user[74]))
        server75 = open_ssh("{}".format(ip[75]),"{}".format(user[75]))
        server76 = open_ssh("{}".format(ip[76]),"{}".format(user[76]))
        server77 = open_ssh("{}".format(ip[77]),"{}".format(user[77]))
        server78 = open_ssh("{}".format(ip[78]),"{}".format(user[78]))
        server79 = open_ssh("{}".format(ip[79]),"{}".format(user[79]))
        server80 = open_ssh("{}".format(ip[80]),"{}".format(user[80]))
        server81 = open_ssh("{}".format(ip[81]),"{}".format(user[81]))
        server82 = open_ssh("{}".format(ip[82]),"{}".format(user[82]))
        server83 = open_ssh("{}".format(ip[83]),"{}".format(user[83]))
        server84 = open_ssh("{}".format(ip[84]),"{}".format(user[84]))
        server85 = open_ssh("{}".format(ip[85]),"{}".format(user[85]))
        server86 = open_ssh("{}".format(ip[86]),"{}".format(user[86]))
        server87 = open_ssh("{}".format(ip[87]),"{}".format(user[87]))
        server88 = open_ssh("{}".format(ip[88]),"{}".format(user[88]))

        time_start2= time.time()
        
        execute_load(server0,slodz,laiks)
        execute_load(server1,slodz,laiks)
        execute_load(server2,slodz,laiks)
        execute_load(server3,slodz,laiks)
        execute_load(server4,slodz,laiks)
        execute_load(server5,slodz,laiks)
        execute_load(server6,slodz,laiks)
        execute_load(server7,slodz,laiks)
        execute_load(server8,slodz,laiks)
        execute_load(server9,slodz,laiks)
        execute_load(server10,slodz,laiks)
        execute_load(server11,slodz,laiks)
        execute_load(server12,slodz,laiks)
        execute_load(server13,slodz,laiks)
        execute_load(server14,slodz,laiks)
        execute_load(server15,slodz,laiks)
        execute_load(server16,slodz,laiks)
        execute_load(server17,slodz,laiks)
        execute_load(server18,slodz,laiks)
        execute_load(server19,slodz,laiks)
        execute_load(server20,slodz,laiks)
        execute_load(server21,slodz,laiks)
        execute_load(server22,slodz,laiks)
        execute_load(server23,slodz,laiks)
        execute_load(server24,slodz,laiks)
        execute_load(server25,slodz,laiks)
        execute_load(server26,slodz,laiks)
        execute_load(server27,slodz,laiks)
        execute_load(server28,slodz,laiks)
        execute_load(server29,slodz,laiks)
        execute_load(server30,slodz,laiks)
        execute_load(server31,slodz,laiks)
        execute_load(server32,slodz,laiks)
        execute_load(server33,slodz,laiks)
        execute_load(server34,slodz,laiks)
        execute_load(server35,slodz,laiks)
        execute_load(server36,slodz,laiks)
        execute_load(server37,slodz,laiks)
        execute_load(server38,slodz,laiks)
        execute_load(server39,slodz,laiks)
        execute_load(server40,slodz,laiks)
        execute_load(server41,slodz,laiks)
        execute_load(server42,slodz,laiks)
        execute_load(server43,slodz,laiks)
        execute_load(server44,slodz,laiks)
        execute_load(server45,slodz,laiks)
        execute_load(server46,slodz,laiks)
        execute_load(server47,slodz,laiks)
        execute_load(server48,slodz,laiks)
        execute_load(server49,slodz,laiks)
        execute_load(server40,slodz,laiks)
        execute_load(server51,slodz,laiks)
        execute_load(server52,slodz,laiks)
        execute_load(server53,slodz,laiks)
        execute_load(server54,slodz,laiks)
        execute_load(server55,slodz,laiks)
        execute_load(server56,slodz,laiks)
        execute_load(server57,slodz,laiks)
        execute_load(server58,slodz,laiks)
        execute_load(server59,slodz,laiks)
        execute_load(server60,slodz,laiks)
        execute_load(server61,slodz,laiks)
        execute_load(server62,slodz,laiks)
        execute_load(server63,slodz,laiks)
        execute_load(server64,slodz,laiks)
        execute_load(server65,slodz,laiks)
        execute_load(server66,slodz,laiks)
        execute_load(server67,slodz,laiks)
        execute_load(server68,slodz,laiks)
        execute_load(server69,slodz,laiks)
        execute_load(server70,slodz,laiks)
        execute_load(server71,slodz,laiks)
        execute_load(server72,slodz,laiks)
        execute_load(server73,slodz,laiks)
        execute_load(server74,slodz,laiks)
        execute_load(server75,slodz,laiks)
        execute_load(server76,slodz,laiks)
        execute_load(server77,slodz,laiks)
        execute_load(server78,slodz,laiks)
        execute_load(server79,slodz,laiks)
        execute_load(server80,slodz,laiks)
        execute_load(server81,slodz,laiks)
        execute_load(server82,slodz,laiks)
        execute_load(server83,slodz,laiks)
        execute_load(server84,slodz,laiks)
        execute_load(server85,slodz,laiks)
        execute_load(server86,slodz,laiks)
        execute_load(server87,slodz,laiks)
        execute_load(server88,slodz,laiks)
        
        time_start3= time.time()
        con = get_connection()
    
        counter=0
        while True:
            insert_database(con,'{}'.format(serveruID[0]), read_temp(server0), slodz)
            insert_database(con,'{}'.format(serveruID[1]), read_temp(server1), slodz)
            insert_database(con,'{}'.format(serveruID[2]), read_temp(server2), slodz)
            insert_database(con,'{}'.format(serveruID[3]), read_temp(server3), slodz)
            insert_database(con,'{}'.format(serveruID[4]), read_temp(server4), slodz)
            insert_database(con,'{}'.format(serveruID[5]), read_temp(server5), slodz)
            insert_database(con,'{}'.format(serveruID[6]), read_temp(server6), slodz)
            insert_database(con,'{}'.format(serveruID[7]), read_temp(server7), slodz)
            insert_database(con,'{}'.format(serveruID[8]), read_temp(server8), slodz)
            insert_database(con,'{}'.format(serveruID[9]), read_temp(server9), slodz)
            insert_database(con,'{}'.format(serveruID[10]), read_temp(server10), slodz)
            insert_database(con,'{}'.format(serveruID[11]), read_temp(server11), slodz)
            insert_database(con,'{}'.format(serveruID[12]), read_temp(server12), slodz)
            insert_database(con,'{}'.format(serveruID[13]), read_temp(server13), slodz)
            insert_database(con,'{}'.format(serveruID[14]), read_temp(server14), slodz)
            insert_database(con,'{}'.format(serveruID[15]), read_temp(server15), slodz)
            insert_database(con,'{}'.format(serveruID[16]), read_temp(server16), slodz)
            insert_database(con,'{}'.format(serveruID[17]), read_temp(server17), slodz)
            insert_database(con,'{}'.format(serveruID[18]), read_temp(server18), slodz)
            insert_database(con,'{}'.format(serveruID[19]), read_temp(server19), slodz)
            insert_database(con,'{}'.format(serveruID[20]), read_temp(server20), slodz)
            insert_database(con,'{}'.format(serveruID[21]), read_temp(server21), slodz)
            insert_database(con,'{}'.format(serveruID[22]), read_temp(server22), slodz)
            insert_database(con,'{}'.format(serveruID[23]), read_temp(server23), slodz)
            insert_database(con,'{}'.format(serveruID[24]), read_temp(server24), slodz)
            insert_database(con,'{}'.format(serveruID[25]), read_temp(server25), slodz)
            insert_database(con,'{}'.format(serveruID[26]), read_temp(server26), slodz)
            insert_database(con,'{}'.format(serveruID[27]), read_temp(server27), slodz)
            insert_database(con,'{}'.format(serveruID[28]), read_temp(server28), slodz)
            insert_database(con,'{}'.format(serveruID[29]), read_temp(server29), slodz)
            insert_database(con,'{}'.format(serveruID[30]), read_temp(server30), slodz)
            insert_database(con,'{}'.format(serveruID[31]), read_temp(server31), slodz)
            insert_database(con,'{}'.format(serveruID[32]), read_temp(server32), slodz)
            insert_database(con,'{}'.format(serveruID[33]), read_temp(server33), slodz)
            insert_database(con,'{}'.format(serveruID[34]), read_temp(server34), slodz)
            insert_database(con,'{}'.format(serveruID[35]), read_temp(server35), slodz)
            insert_database(con,'{}'.format(serveruID[36]), read_temp(server36), slodz)
            insert_database(con,'{}'.format(serveruID[37]), read_temp(server37), slodz)
            insert_database(con,'{}'.format(serveruID[38]), read_temp(server38), slodz)
            insert_database(con,'{}'.format(serveruID[39]), read_temp(server39), slodz)
            insert_database(con,'{}'.format(serveruID[40]), read_temp(server40), slodz)
            insert_database(con,'{}'.format(serveruID[41]), read_temp(server41), slodz)
            insert_database(con,'{}'.format(serveruID[42]), read_temp(server42), slodz)
            insert_database(con,'{}'.format(serveruID[43]), read_temp(server43), slodz)
            insert_database(con,'{}'.format(serveruID[44]), read_temp(server44), slodz)
            insert_database(con,'{}'.format(serveruID[45]), read_temp(server45), slodz)
            insert_database(con,'{}'.format(serveruID[46]), read_temp(server46), slodz)
            insert_database(con,'{}'.format(serveruID[47]), read_temp(server47), slodz)
            insert_database(con,'{}'.format(serveruID[48]), read_temp(server48), slodz)
            insert_database(con,'{}'.format(serveruID[49]), read_temp(server49), slodz)
            insert_database(con,'{}'.format(serveruID[50]), read_temp(server50), slodz)
            insert_database(con,'{}'.format(serveruID[51]), read_temp(server51), slodz)
            insert_database(con,'{}'.format(serveruID[52]), read_temp(server52), slodz)
            insert_database(con,'{}'.format(serveruID[53]), read_temp(server53), slodz)
            insert_database(con,'{}'.format(serveruID[54]), read_temp(server54), slodz)
            insert_database(con,'{}'.format(serveruID[55]), read_temp(server55), slodz)
            insert_database(con,'{}'.format(serveruID[56]), read_temp(server56), slodz)
            insert_database(con,'{}'.format(serveruID[57]), read_temp(server57), slodz)
            insert_database(con,'{}'.format(serveruID[58]), read_temp(server58), slodz)
            insert_database(con,'{}'.format(serveruID[59]), read_temp(server59), slodz)
            insert_database(con,'{}'.format(serveruID[60]), read_temp(server60), slodz)
            insert_database(con,'{}'.format(serveruID[61]), read_temp(server61), slodz)
            insert_database(con,'{}'.format(serveruID[62]), read_temp(server62), slodz)
            insert_database(con,'{}'.format(serveruID[63]), read_temp(server63), slodz)
            insert_database(con,'{}'.format(serveruID[64]), read_temp(server64), slodz)
            insert_database(con,'{}'.format(serveruID[65]), read_temp(server65), slodz)
            insert_database(con,'{}'.format(serveruID[66]), read_temp(server66), slodz)
            insert_database(con,'{}'.format(serveruID[67]), read_temp(server67), slodz)
            insert_database(con,'{}'.format(serveruID[68]), read_temp(server68), slodz)
            insert_database(con,'{}'.format(serveruID[69]), read_temp(server69), slodz)
            insert_database(con,'{}'.format(serveruID[70]), read_temp(server70), slodz)
            insert_database(con,'{}'.format(serveruID[71]), read_temp(server71), slodz)
            insert_database(con,'{}'.format(serveruID[72]), read_temp(server72), slodz)
            insert_database(con,'{}'.format(serveruID[73]), read_temp(server73), slodz)
            insert_database(con,'{}'.format(serveruID[74]), read_temp(server74), slodz)
            insert_database(con,'{}'.format(serveruID[75]), read_temp(server75), slodz)
            insert_database(con,'{}'.format(serveruID[76]), read_temp(server76), slodz)
            insert_database(con,'{}'.format(serveruID[77]), read_temp(server77), slodz)
            insert_database(con,'{}'.format(serveruID[78]), read_temp(server78), slodz)
            insert_database(con,'{}'.format(serveruID[79]), read_temp(server79), slodz)
            insert_database(con,'{}'.format(serveruID[80]), read_temp(server80), slodz)
            insert_database(con,'{}'.format(serveruID[81]), read_temp(server81), slodz)
            insert_database(con,'{}'.format(serveruID[82]), read_temp(server82), slodz)
            insert_database(con,'{}'.format(serveruID[83]), read_temp(server83), slodz)
            insert_database(con,'{}'.format(serveruID[84]), read_temp(server84), slodz)
            insert_database(con,'{}'.format(serveruID[85]), read_temp(server85), slodz)
            insert_database(con,'{}'.format(serveruID[86]), read_temp(server86), slodz)
            insert_database(con,'{}'.format(serveruID[87]), read_temp(server87), slodz)
            insert_database(con,'{}'.format(serveruID[88]), read_temp(server88), slodz)
            time.sleep(4.1)
            counter+=1
            if counter == int(laiks)*3:
                print('stoping')
                break 

        time_start4= time.time()
        print('open ssh: ',time_start2-time_start1)
        print('slodze: ',time_start3-time_start2)
        print('nolasisana: ',time_start4-time_start3)
        print('kopeejais: ', time_start4-time_start1)
        update_testugrafiks(grafiksId,'pabeigts')
        close_connection(con)

        close_ssh(server0)
        close_ssh(server1)
        close_ssh(server2)
        close_ssh(server3)
        close_ssh(server4)
        close_ssh(server5)
        close_ssh(server6)
        close_ssh(server7)
        close_ssh(server8)
        close_ssh(server9)
        close_ssh(server10)
        close_ssh(server11)
        close_ssh(server12)
        close_ssh(server13)
        close_ssh(server14)
        close_ssh(server15)
        close_ssh(server16)
        close_ssh(server17)
        close_ssh(server18)
        close_ssh(server19)
        close_ssh(server20)
        close_ssh(server21)
        close_ssh(server22)
        close_ssh(server23)
        close_ssh(server24)
        close_ssh(server25)
        close_ssh(server26)
        close_ssh(server27)
        close_ssh(server28)
        close_ssh(server29)
        close_ssh(server30)
        close_ssh(server31)
        close_ssh(server32)
        close_ssh(server33)
        close_ssh(server34)
        close_ssh(server35)
        close_ssh(server36)
        close_ssh(server37)
        close_ssh(server38)
        close_ssh(server39)
        close_ssh(server40)
        close_ssh(server41)
        close_ssh(server42)
        close_ssh(server43)
        close_ssh(server44)
        close_ssh(server45)
        close_ssh(server46)
        close_ssh(server47)
        close_ssh(server48)
        close_ssh(server49)
        close_ssh(server50)
        close_ssh(server51)
        close_ssh(server52)
        close_ssh(server53)
        close_ssh(server54)
        close_ssh(server55)
        close_ssh(server56)
        close_ssh(server57)
        close_ssh(server58)
        close_ssh(server59)
        close_ssh(server60)
        close_ssh(server61)
        close_ssh(server62)
        close_ssh(server63)
        close_ssh(server64)
        close_ssh(server65)
        close_ssh(server66)
        close_ssh(server67)
        close_ssh(server68)
        close_ssh(server69)
        close_ssh(server70)
        close_ssh(server71)
        close_ssh(server72)
        close_ssh(server73)
        close_ssh(server74)
        close_ssh(server75)
        close_ssh(server76)
        close_ssh(server77)
        close_ssh(server78)
        close_ssh(server79)
        close_ssh(server80)
        close_ssh(server81)
        close_ssh(server82)
        close_ssh(server83)
        close_ssh(server84)
        close_ssh(server85)
        close_ssh(server86)
        close_ssh(server87)
        close_ssh(server88)
        
    else:
        # Ja nav aktīvu testu, vai arī nav testu tuvākajā laikā, tad tiek gaidītas 15 sekundes, līdz tiek nolasīts nākošais tests
        print("Šobrīd nav paredzētu testu!")
        time.sleep(15)
