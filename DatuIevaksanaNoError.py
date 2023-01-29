#!/usr/bin/env python
# coding: utf-8

# In[3]:


import paramiko
import time
import pandas as pd
from collections import defaultdict
import psycopg2
import config
import datetime
from datetime import datetime, timedelta

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
    grafiksid=''
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
            if grafiksid == '':    
                grafiksid='003249d6-b520-4191-a623-21fc77c04344'
                skapji='1'
                datetime_object=str(datetime.now())[0:16] # errors tiek ievadits ka string nevis ka datums
                datetime_object=datetime_object[0:2]+"22"+datetime_object[4:]
                datums=datetime_object[8:10]+'-'+datetime_object[5:7]+'-'+datetime_object[0:4]+""+datetime_object[10:]
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
    grafiksId=''
    
    skapis1='8d674cc5-56be-40db-a51c-5db5ca2555ad'
    skapis2='42032aad-deee-45a3-a4a7-40a3c9336a74'
    skapis3='28e52f26-80c7-41bb-aa5b-33c81c9df88c'

    # Nolasa no Testu grafika - Grafika ID, Skapjus, kuriem jāveic testi, datumu, laiku, slodzi
    grafiksId,skapji,datums,laiks,slodz=read_database_testinfo()
    
    CurrentDate = str(datetime.now())[0:16]
    ExpectedDate = datums#datetime.strptime(datums, "%d-%m-%Y %H:%M:%S")
    ExpectedDateFiveBehind=str(ExpectedDate)[0:16]
    ExpectedDateFiveInfront=str(ExpectedDate)[0:16]    
    if datums =='':
        print("VPN ERROR!")
        break
    
    
    # Izveidoju vienkāršāku veidu, kas atļauj veikt testu 5min pirms vai pēc testa veikšanas laika
    dt_test = datetime.now()  
    ExpectedDateinfront1 = datetime.strptime(datums, '%d-%m-%Y %H:%M') + timedelta(minutes=5)
    ExpectedDatebehind1 = datetime.strptime(datums, '%d-%m-%Y %H:%M') - timedelta(minutes=5)

    # Tiek pārbaudīts vai tests ir tuvāko 5 min., laikā
    # Ja tas ir, tad tiek pārbaudīts, kuriem serveru skapjiem tiek veikti testi
    # Kā arī iegūts serveru skapju info.
    
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
        skapis1_server1 = open_ssh("{}".format(ip[0]),"{}".format(user[0]))
        skapis1_server2 = open_ssh("{}".format(ip[1]),"{}".format(user[1]))
        skapis1_server3 = open_ssh("{}".format(ip[2]),"{}".format(user[2]))
        skapis1_server4 = open_ssh("{}".format(ip[3]),"{}".format(user[3]))
        skapis1_server5 = open_ssh("{}".format(ip[4]),"{}".format(user[4]))
        skapis1_server6 = open_ssh("{}".format(ip[5]),"{}".format(user[5]))
        skapis1_server7 = open_ssh("{}".format(ip[6]),"{}".format(user[6]))
        skapis1_server8 = open_ssh("{}".format(ip[7]),"{}".format(user[7]))
        skapis1_server9 = open_ssh("{}".format(ip[8]),"{}".format(user[8]))
        skapis1_server10 = open_ssh("{}".format(ip[9]),"{}".format(user[9]))
        skapis1_server11 = open_ssh("{}".format(ip[10]),"{}".format(user[10]))
        skapis1_server12 = open_ssh("{}".format(ip[11]),"{}".format(user[11]))
        skapis1_server13 = open_ssh("{}".format(ip[12]),"{}".format(user[12]))
        skapis1_server14 = open_ssh("{}".format(ip[13]),"{}".format(user[13]))
        skapis1_server15 = open_ssh("{}".format(ip[14]),"{}".format(user[14]))
        skapis1_server16 = open_ssh("{}".format(ip[15]),"{}".format(user[15]))
        skapis1_server17 = open_ssh("{}".format(ip[16]),"{}".format(user[16]))
        skapis1_server18 = open_ssh("{}".format(ip[17]),"{}".format(user[17]))
        skapis1_server19 = open_ssh("{}".format(ip[18]),"{}".format(user[18]))
        skapis1_server20 = open_ssh("{}".format(ip[19]),"{}".format(user[19]))
        skapis1_server21 = open_ssh("{}".format(ip[20]),"{}".format(user[20]))
        skapis1_server22 = open_ssh("{}".format(ip[21]),"{}".format(user[21]))
        skapis1_server23 = open_ssh("{}".format(ip[22]),"{}".format(user[22]))
        skapis1_server24 = open_ssh("{}".format(ip[23]),"{}".format(user[23]))
        skapis1_server25 = open_ssh("{}".format(ip[24]),"{}".format(user[24]))
        skapis1_server26 = open_ssh("{}".format(ip[25]),"{}".format(user[25]))
        skapis1_server27 = open_ssh("{}".format(ip[26]),"{}".format(user[26]))
        skapis1_server28 = open_ssh("{}".format(ip[27]),"{}".format(user[27]))
        skapis1_server29 = open_ssh("{}".format(ip[28]),"{}".format(user[28]))
    
        skapis2_server1 = open_ssh("{}".format(ip[29]),"{}".format(user[29]))
        skapis2_server2 = open_ssh("{}".format(ip[30]),"{}".format(user[30]))
        skapis2_server3 = open_ssh("{}".format(ip[31]),"{}".format(user[31]))
        skapis2_server4 = open_ssh("{}".format(ip[32]),"{}".format(user[32]))
        skapis2_server5 = open_ssh("{}".format(ip[33]),"{}".format(user[33]))
        skapis2_server6 = open_ssh("{}".format(ip[34]),"{}".format(user[34]))
        skapis2_server7 = open_ssh("{}".format(ip[35]),"{}".format(user[35]))
        skapis2_server8 = open_ssh("{}".format(ip[36]),"{}".format(user[36]))
        skapis2_server9 = open_ssh("{}".format(ip[37]),"{}".format(user[37]))
        skapis2_server10 = open_ssh("{}".format(ip[38]),"{}".format(user[38]))
        skapis2_server11 = open_ssh("{}".format(ip[39]),"{}".format(user[39]))
        skapis2_server12 = open_ssh("{}".format(ip[40]),"{}".format(user[40]))
        skapis2_server13 = open_ssh("{}".format(ip[41]),"{}".format(user[41]))
        skapis2_server14 = open_ssh("{}".format(ip[42]),"{}".format(user[42]))
        skapis2_server15 = open_ssh("{}".format(ip[43]),"{}".format(user[43]))
        skapis2_server16 = open_ssh("{}".format(ip[44]),"{}".format(user[44]))
        skapis2_server17 = open_ssh("{}".format(ip[45]),"{}".format(user[45]))
        skapis2_server18 = open_ssh("{}".format(ip[46]),"{}".format(user[46]))
        skapis2_server19 = open_ssh("{}".format(ip[47]),"{}".format(user[47]))
        skapis2_server20 = open_ssh("{}".format(ip[48]),"{}".format(user[48]))
        skapis2_server21 = open_ssh("{}".format(ip[49]),"{}".format(user[49]))
        skapis2_server22 = open_ssh("{}".format(ip[50]),"{}".format(user[50]))
        skapis2_server23 = open_ssh("{}".format(ip[51]),"{}".format(user[51]))
        skapis2_server24 = open_ssh("{}".format(ip[52]),"{}".format(user[52]))
        skapis2_server25 = open_ssh("{}".format(ip[53]),"{}".format(user[53]))
        skapis2_server26 = open_ssh("{}".format(ip[54]),"{}".format(user[54]))
        skapis2_server27 = open_ssh("{}".format(ip[55]),"{}".format(user[55]))
        skapis2_server28 = open_ssh("{}".format(ip[56]),"{}".format(user[56]))
        skapis2_server29 = open_ssh("{}".format(ip[57]),"{}".format(user[57]))
        skapis2_server30 = open_ssh("{}".format(ip[58]),"{}".format(user[58]))
        
        skapis3_server1 = open_ssh("{}".format(ip[59]),"{}".format(user[59]))
        skapis3_server2 = open_ssh("{}".format(ip[60]),"{}".format(user[60]))
        skapis3_server3 = open_ssh("{}".format(ip[61]),"{}".format(user[61]))
        skapis3_server4 = open_ssh("{}".format(ip[62]),"{}".format(user[62]))
        skapis3_server5 = open_ssh("{}".format(ip[63]),"{}".format(user[63]))
        skapis3_server6 = open_ssh("{}".format(ip[64]),"{}".format(user[64]))
        skapis3_server7 = open_ssh("{}".format(ip[65]),"{}".format(user[65]))
        skapis3_server8 = open_ssh("{}".format(ip[66]),"{}".format(user[66]))
        skapis3_server9 = open_ssh("{}".format(ip[67]),"{}".format(user[67]))
        skapis3_server10 = open_ssh("{}".format(ip[68]),"{}".format(user[68]))
        skapis3_server11 = open_ssh("{}".format(ip[69]),"{}".format(user[69]))
        skapis3_server12 = open_ssh("{}".format(ip[70]),"{}".format(user[70]))
        skapis3_server13 = open_ssh("{}".format(ip[71]),"{}".format(user[71]))
        skapis3_server14 = open_ssh("{}".format(ip[72]),"{}".format(user[72]))
        skapis3_server15 = open_ssh("{}".format(ip[73]),"{}".format(user[73]))
        skapis3_server16 = open_ssh("{}".format(ip[74]),"{}".format(user[74]))
        skapis3_server17 = open_ssh("{}".format(ip[75]),"{}".format(user[75]))
        skapis3_server18 = open_ssh("{}".format(ip[76]),"{}".format(user[76]))
        skapis3_server19 = open_ssh("{}".format(ip[77]),"{}".format(user[77]))
        skapis3_server20 = open_ssh("{}".format(ip[78]),"{}".format(user[78]))
        skapis3_server21 = open_ssh("{}".format(ip[79]),"{}".format(user[79]))
        skapis3_server22 = open_ssh("{}".format(ip[80]),"{}".format(user[80]))
        skapis3_server23 = open_ssh("{}".format(ip[81]),"{}".format(user[81]))
        skapis3_server24 = open_ssh("{}".format(ip[82]),"{}".format(user[82]))
        skapis3_server25 = open_ssh("{}".format(ip[83]),"{}".format(user[83]))
        skapis3_server26 = open_ssh("{}".format(ip[84]),"{}".format(user[84]))
        skapis3_server27 = open_ssh("{}".format(ip[85]),"{}".format(user[85]))
        skapis3_server28 = open_ssh("{}".format(ip[86]),"{}".format(user[86]))
        skapis3_server29 = open_ssh("{}".format(ip[87]),"{}".format(user[87]))
        skapis3_server30 = open_ssh("{}".format(ip[88]),"{}".format(user[88]))
        
        
        #Janolasa IDLE TEMP, un tad var likt slodzi
        
        time_start2= time.time()
        

        execute_load(skapis1_server1,slodz[1],laiks)
        execute_load(skapis1_server2,slodz[1],laiks)
        execute_load(skapis1_server3,slodz[1],laiks)
        execute_load(skapis1_server4,slodz[1],laiks)
        execute_load(skapis1_server5,slodz[1],laiks)
        execute_load(skapis1_server6,slodz[1],laiks)
        execute_load(skapis1_server7,slodz[1],laiks)
        execute_load(skapis1_server8,slodz[1],laiks)
        execute_load(skapis1_server9,slodz[1],laiks)
        execute_load(skapis1_server10,slodz[1],laiks)
        execute_load(skapis1_server11,slodz[1],laiks)
        execute_load(skapis1_server13,slodz[1],laiks)
        execute_load(skapis1_server14,slodz[1],laiks)
        execute_load(skapis1_server15,slodz[1],laiks)
        execute_load(skapis1_server16,slodz[1],laiks)
        execute_load(skapis1_server17,slodz[1],laiks)
        execute_load(skapis1_server18,slodz[1],laiks)
        execute_load(skapis1_server19,slodz[1],laiks)
        execute_load(skapis1_server20,slodz[1],laiks)
        execute_load(skapis1_server21,slodz[1],laiks)
        execute_load(skapis1_server23,slodz[1],laiks)
        execute_load(skapis1_server24,slodz[1],laiks)
        execute_load(skapis1_server25,slodz[1],laiks)
        execute_load(skapis1_server26,slodz[1],laiks)
        execute_load(skapis1_server27,slodz[1],laiks)
        execute_load(skapis1_server28,slodz[1],laiks)
        execute_load(skapis1_server29,slodz[1],laiks)
        
        execute_load(skapis2_server1,slodz[2],laiks)
        execute_load(skapis2_server2,slodz[2],laiks)
        execute_load(skapis2_server3,slodz[2],laiks)
        execute_load(skapis2_server4,slodz[2],laiks)
        execute_load(skapis2_server5,slodz[2],laiks)
        execute_load(skapis2_server6,slodz[2],laiks)
        execute_load(skapis2_server7,slodz[2],laiks)
        execute_load(skapis2_server8,slodz[2],laiks)
        execute_load(skapis2_server9,slodz[2],laiks)
        execute_load(skapis2_server10,slodz[2],laiks)
        execute_load(skapis2_server11,slodz[2],laiks)
        execute_load(skapis2_server13,slodz[2],laiks)
        execute_load(skapis2_server14,slodz[2],laiks)
        execute_load(skapis2_server15,slodz[2],laiks)
        execute_load(skapis2_server16,slodz[2],laiks)
        execute_load(skapis2_server17,slodz[2],laiks)
        execute_load(skapis2_server18,slodz[2],laiks)
        execute_load(skapis2_server19,slodz[2],laiks)
        execute_load(skapis2_server20,slodz[2],laiks)
        execute_load(skapis2_server21,slodz[2],laiks)
        execute_load(skapis2_server23,slodz[2],laiks)
        execute_load(skapis2_server24,slodz[2],laiks)
        execute_load(skapis2_server25,slodz[2],laiks)
        execute_load(skapis2_server26,slodz[2],laiks)
        execute_load(skapis2_server27,slodz[2],laiks)
        execute_load(skapis2_server28,slodz[2],laiks)
        execute_load(skapis2_server29,slodz[2],laiks)
        execute_load(skapis2_server30,slodz[2],laiks)
    
        execute_load(skapis3_server1,slodz[3],laiks)
        execute_load(skapis3_server2,slodz[3],laiks)
        execute_load(skapis3_server3,slodz[3],laiks)
        execute_load(skapis3_server4,slodz[3],laiks)
        execute_load(skapis3_server5,slodz[3],laiks)
        execute_load(skapis3_server6,slodz[3],laiks)
        execute_load(skapis3_server7,slodz[3],laiks)
        execute_load(skapis3_server8,slodz[3],laiks)
        execute_load(skapis3_server9,slodz[3],laiks)
        execute_load(skapis3_server10,slodz[3],laiks)
        execute_load(skapis3_server11,slodz[3],laiks)
        execute_load(skapis3_server13,slodz[3],laiks)
        execute_load(skapis3_server14,slodz[3],laiks)
        execute_load(skapis3_server15,slodz[3],laiks)
        execute_load(skapis3_server16,slodz[3],laiks)
        execute_load(skapis3_server17,slodz[3],laiks)
        execute_load(skapis3_server18,slodz[3],laiks)
        execute_load(skapis3_server19,slodz[3],laiks)
        execute_load(skapis3_server20,slodz[3],laiks)
        execute_load(skapis3_server21,slodz[3],laiks)
        execute_load(skapis3_server23,slodz[3],laiks)
        execute_load(skapis3_server24,slodz[3],laiks)
        execute_load(skapis3_server25,slodz[3],laiks)
        execute_load(skapis3_server26,slodz[3],laiks)
        execute_load(skapis3_server27,slodz[3],laiks)
        execute_load(skapis3_server28,slodz[3],laiks)
        execute_load(skapis3_server29,slodz[3],laiks)
        execute_load(skapis3_server30,slodz[3],laiks)
        
        time_start3= time.time()
        con = get_connection()
    
        counter=0
        while True:
            insert_database(con,'{}'.format(serveruID[0]), read_temp(skapis1_server1), slodz[1])
            insert_database(con,'{}'.format(serveruID[1]), read_temp(skapis1_server2), slodz[1])
            insert_database(con,'{}'.format(serveruID[2]), read_temp(skapis1_server3), slodz[1])
            insert_database(con,'{}'.format(serveruID[3]), read_temp(skapis1_server4), slodz[1])
            insert_database(con,'{}'.format(serveruID[4]), read_temp(skapis1_server5), slodz[1])
            insert_database(con,'{}'.format(serveruID[5]), read_temp(skapis1_server6), slodz[1])
            insert_database(con,'{}'.format(serveruID[6]), read_temp(skapis1_server7), slodz[1])
            insert_database(con,'{}'.format(serveruID[7]), read_temp(skapis1_server8), slodz[1])
            insert_database(con,'{}'.format(serveruID[8]), read_temp(skapis1_server9), slodz[1])
            insert_database(con,'{}'.format(serveruID[9]), read_temp(skapis1_server10), slodz[1])
            insert_database(con,'{}'.format(serveruID[10]), read_temp(skapis1_server11), slodz[1])
            insert_database(con,'{}'.format(serveruID[11]), read_temp(skapis1_server12), slodz[1])
            insert_database(con,'{}'.format(serveruID[12]), read_temp(skapis1_server13), slodz[1])
            insert_database(con,'{}'.format(serveruID[13]), read_temp(skapis1_server14), slodz[1])
            insert_database(con,'{}'.format(serveruID[14]), read_temp(skapis1_server15), slodz[1])
            insert_database(con,'{}'.format(serveruID[15]), read_temp(skapis1_server16), slodz[1])
            insert_database(con,'{}'.format(serveruID[16]), read_temp(skapis1_server17), slodz[1])
            insert_database(con,'{}'.format(serveruID[17]), read_temp(skapis1_server18), slodz[1])
            insert_database(con,'{}'.format(serveruID[18]), read_temp(skapis1_server19), slodz[1])
            insert_database(con,'{}'.format(serveruID[19]), read_temp(skapis1_server20), slodz[1])
            insert_database(con,'{}'.format(serveruID[20]), read_temp(skapis1_server21), slodz[1])
            insert_database(con,'{}'.format(serveruID[21]), read_temp(skapis1_server22), slodz[1])
            insert_database(con,'{}'.format(serveruID[22]), read_temp(skapis1_server23), slodz[1])
            insert_database(con,'{}'.format(serveruID[23]), read_temp(skapis1_server24), slodz[1])
            insert_database(con,'{}'.format(serveruID[24]), read_temp(skapis1_server25), slodz[1])
            insert_database(con,'{}'.format(serveruID[25]), read_temp(skapis1_server26), slodz[1])
            insert_database(con,'{}'.format(serveruID[26]), read_temp(skapis1_server27), slodz[1])
            insert_database(con,'{}'.format(serveruID[27]), read_temp(skapis1_server28), slodz[1])
            insert_database(con,'{}'.format(serveruID[28]), read_temp(skapis1_server29), slodz[1])
        
            insert_database(con,'{}'.format(serveruID[29]), read_temp(skapis2_server1), slodz[2])
            insert_database(con,'{}'.format(serveruID[30]), read_temp(skapis2_server2), slodz[2])
            insert_database(con,'{}'.format(serveruID[31]), read_temp(skapis2_server3), slodz[2])
            insert_database(con,'{}'.format(serveruID[32]), read_temp(skapis2_server4), slodz[2])
            insert_database(con,'{}'.format(serveruID[33]), read_temp(skapis2_server5), slodz[2])
            insert_database(con,'{}'.format(serveruID[34]), read_temp(skapis2_server6), slodz[2])
            insert_database(con,'{}'.format(serveruID[35]), read_temp(skapis2_server7), slodz[2])
            insert_database(con,'{}'.format(serveruID[36]), read_temp(skapis2_server8), slodz[2])
            insert_database(con,'{}'.format(serveruID[37]), read_temp(skapis2_server9), slodz[2])
            insert_database(con,'{}'.format(serveruID[38]), read_temp(skapis2_server10), slodz[2])
            insert_database(con,'{}'.format(serveruID[39]), read_temp(skapis2_server11), slodz[2])
            insert_database(con,'{}'.format(serveruID[40]), read_temp(skapis2_server12), slodz[2])
            insert_database(con,'{}'.format(serveruID[41]), read_temp(skapis2_server13), slodz[2])
            insert_database(con,'{}'.format(serveruID[42]), read_temp(skapis2_server14), slodz[2])
            insert_database(con,'{}'.format(serveruID[43]), read_temp(skapis2_server15), slodz[2])
            insert_database(con,'{}'.format(serveruID[44]), read_temp(skapis2_server16), slodz[2])
            insert_database(con,'{}'.format(serveruID[45]), read_temp(skapis2_server17), slodz[2])
            insert_database(con,'{}'.format(serveruID[46]), read_temp(skapis2_server18), slodz[2])
            insert_database(con,'{}'.format(serveruID[47]), read_temp(skapis2_server19), slodz[2])
            insert_database(con,'{}'.format(serveruID[48]), read_temp(skapis2_server20), slodz[2])
            insert_database(con,'{}'.format(serveruID[49]), read_temp(skapis2_server21), slodz[2])
            insert_database(con,'{}'.format(serveruID[50]), read_temp(skapis2_server22), slodz[2])
            insert_database(con,'{}'.format(serveruID[51]), read_temp(skapis2_server23), slodz[2])
            insert_database(con,'{}'.format(serveruID[52]), read_temp(skapis2_server24), slodz[2])
            insert_database(con,'{}'.format(serveruID[53]), read_temp(skapis2_server25), slodz[2])
            insert_database(con,'{}'.format(serveruID[54]), read_temp(skapis2_server26), slodz[2])
            insert_database(con,'{}'.format(serveruID[55]), read_temp(skapis2_server27), slodz[2])
            insert_database(con,'{}'.format(serveruID[56]), read_temp(skapis2_server28), slodz[2])
            insert_database(con,'{}'.format(serveruID[57]), read_temp(skapis2_server29), slodz[2])
            insert_database(con,'{}'.format(serveruID[58]), read_temp(skapis2_server30), slodz[2])
            
            insert_database(con,'{}'.format(serveruID[59]), read_temp(skapis3_server1), slodz[3])
            insert_database(con,'{}'.format(serveruID[60]), read_temp(skapis3_server2), slodz[3])
            insert_database(con,'{}'.format(serveruID[61]), read_temp(skapis3_server3), slodz[3])
            insert_database(con,'{}'.format(serveruID[62]), read_temp(skapis3_server4), slodz[3])
            insert_database(con,'{}'.format(serveruID[63]), read_temp(skapis3_server5), slodz[3])
            insert_database(con,'{}'.format(serveruID[64]), read_temp(skapis3_server6), slodz[3])
            insert_database(con,'{}'.format(serveruID[65]), read_temp(skapis3_server7), slodz[3])
            insert_database(con,'{}'.format(serveruID[66]), read_temp(skapis3_server8), slodz[3])
            insert_database(con,'{}'.format(serveruID[67]), read_temp(skapis3_server9), slodz[3])
            insert_database(con,'{}'.format(serveruID[68]), read_temp(skapis3_server10), slodz[3])
            insert_database(con,'{}'.format(serveruID[69]), read_temp(skapis3_server11), slodz[3])
            insert_database(con,'{}'.format(serveruID[70]), read_temp(skapis3_server12), slodz[3])
            insert_database(con,'{}'.format(serveruID[71]), read_temp(skapis3_server13), slodz[3])
            insert_database(con,'{}'.format(serveruID[72]), read_temp(skapis3_server14), slodz[3])
            insert_database(con,'{}'.format(serveruID[73]), read_temp(skapis3_server15), slodz[3])
            insert_database(con,'{}'.format(serveruID[74]), read_temp(skapis3_server16), slodz[3])
            insert_database(con,'{}'.format(serveruID[75]), read_temp(skapis3_server17), slodz[3])
            insert_database(con,'{}'.format(serveruID[76]), read_temp(skapis3_server18), slodz[3])
            insert_database(con,'{}'.format(serveruID[77]), read_temp(skapis3_server19), slodz[3])
            insert_database(con,'{}'.format(serveruID[78]), read_temp(skapis3_server20), slodz[3])
            insert_database(con,'{}'.format(serveruID[79]), read_temp(skapis3_server21), slodz[3])
            insert_database(con,'{}'.format(serveruID[80]), read_temp(skapis3_server22), slodz[3])
            insert_database(con,'{}'.format(serveruID[81]), read_temp(skapis3_server23), slodz[3])
            insert_database(con,'{}'.format(serveruID[82]), read_temp(skapis3_server24), slodz[3])
            insert_database(con,'{}'.format(serveruID[83]), read_temp(skapis3_server25), slodz[3])
            insert_database(con,'{}'.format(serveruID[84]), read_temp(skapis3_server26), slodz[3])
            insert_database(con,'{}'.format(serveruID[85]), read_temp(skapis3_server27), slodz[3])
            insert_database(con,'{}'.format(serveruID[86]), read_temp(skapis3_server28), slodz[3])
            insert_database(con,'{}'.format(serveruID[87]), read_temp(skapis3_server29), slodz[3])
            insert_database(con,'{}'.format(serveruID[88]), read_temp(skapis3_server30), slodz[3])
            time.sleep(4.325)
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

        close_ssh(skapis1_server1)
        close_ssh(skapis1_server2)
        close_ssh(skapis1_server3)
        close_ssh(skapis1_server4)
        close_ssh(skapis1_server5)
        close_ssh(skapis1_server6)
        close_ssh(skapis1_server7)
        close_ssh(skapis1_server8)
        close_ssh(skapis1_server9)
        close_ssh(skapis1_server10)
        close_ssh(skapis1_server11)
        close_ssh(skapis1_server12)
        close_ssh(skapis1_server13)
        close_ssh(skapis1_server14)
        close_ssh(skapis1_server15)
        close_ssh(skapis1_server16)
        close_ssh(skapis1_server17)
        close_ssh(skapis1_server18)
        close_ssh(skapis1_server19)
        close_ssh(skapis1_server20)
        close_ssh(skapis1_server21)
        close_ssh(skapis1_server22)
        close_ssh(skapis1_server23)
        close_ssh(skapis1_server24)
        close_ssh(skapis1_server25)
        close_ssh(skapis1_server26)
        close_ssh(skapis1_server27)
        close_ssh(skapis1_server28)
        close_ssh(skapis1_server29)
        
        close_ssh(skapis2_server1)
        close_ssh(skapis2_server2)
        close_ssh(skapis2_server3)
        close_ssh(skapis2_server4)
        close_ssh(skapis2_server5)
        close_ssh(skapis2_server6)
        close_ssh(skapis2_server7)
        close_ssh(skapis2_server8)
        close_ssh(skapis2_server9)
        close_ssh(skapis2_server10)
        close_ssh(skapis2_server11)
        close_ssh(skapis2_server12)
        close_ssh(skapis2_server13)
        close_ssh(skapis2_server14)
        close_ssh(skapis2_server15)
        close_ssh(skapis2_server16)
        close_ssh(skapis2_server17)
        close_ssh(skapis2_server18)
        close_ssh(skapis2_server19)
        close_ssh(skapis2_server20)
        close_ssh(skapis2_server21)
        close_ssh(skapis2_server22)
        close_ssh(skapis2_server23)
        close_ssh(skapis2_server24)
        close_ssh(skapis2_server25)
        close_ssh(skapis2_server26)
        close_ssh(skapis2_server27)
        close_ssh(skapis2_server28)
        close_ssh(skapis2_server29)
        close_ssh(skapis2_server30)
    
        close_ssh(skapis3_server1)
        close_ssh(skapis3_server2)
        close_ssh(skapis3_server3)
        close_ssh(skapis3_server4)
        close_ssh(skapis3_server5)
        close_ssh(skapis3_server6)
        close_ssh(skapis3_server7)
        close_ssh(skapis3_server8)
        close_ssh(skapis3_server9)
        close_ssh(skapis3_server10)
        close_ssh(skapis3_server11)
        close_ssh(skapis3_server12)
        close_ssh(skapis3_server13)
        close_ssh(skapis3_server14)
        close_ssh(skapis3_server15)
        close_ssh(skapis3_server16)
        close_ssh(skapis3_server17)
        close_ssh(skapis3_server18)
        close_ssh(skapis3_server19)
        close_ssh(skapis3_server20)
        close_ssh(skapis3_server21)
        close_ssh(skapis3_server22)
        close_ssh(skapis3_server23)
        close_ssh(skapis3_server24)
        close_ssh(skapis3_server25)
        close_ssh(skapis3_server26)
        close_ssh(skapis3_server27)
        close_ssh(skapis3_server28)
        close_ssh(skapis3_server29)
        close_ssh(skapis3_server30)
        
    else:
        dt_after = datetime.now()  
        result_dt_after = dt_after - timedelta(minutes=15)  
        if result_dt_after > ExpectedDatebehind1:
            # Ja nav dummy dati, tad atcelt testu
            if grafiksId != '003249d6-b520-4191-a623-21fc77c04344':
                print("Atcelts tests, kura ID: ", grafiksId)
                update_testugrafiks(grafiksId, 'atcelts')
        # Ja nav aktīvu testu, vai arī nav testu tuvākajā laikā, 
        # tad tiek gaidītas 15 sekundes, līdz tiek nolasīts nākošais tests
        print("Šobrīd nav paredzētu testu!")
        time.sleep(15)


# In[8]:


from datetime import datetime, timedelta
dt_test = datetime.now()
datums = "27/01/2023 10:45:00"
print(datums)
ExpectedDateinfront1 = datetime.strptime(datums, '%d/%m/%Y %H:%M:%S') + timedelta(minutes=5)
ExpectedDatebehind1 = datetime.strptime(datums, '%d/%m/%Y %H:%M:%S') - timedelta(minutes=5)
print(ExpectedDatebehind1)


# In[ ]:




