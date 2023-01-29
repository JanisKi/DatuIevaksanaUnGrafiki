import paramiko
import time
import pandas as pd
from collections import defaultdict
import psycopg2
import config
import datetime
from datetime import datetime
import matplotlib.pyplot as plt



def get_connection():
    connection = psycopg2.connect(user="rtu170",
                                  password="deac2022",
                                  host="192.168.99.165",
                                  port="5432",
                                  database="ExDatiDB")
    return connection


# Aizver savienojumu ar datu bāzi
def close_connection(connection):
    if connection:
        connection.close()

def read_database():
    laiks=[]
    dati=[]
    sensorid=[]
    try:
        connection = get_connection()
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from zabbixdati"
        cursor.execute(postgreSQL_select_Query)
        exdatidb = cursor.fetchall()

        for row in exdatidb:
            laiks.append(row[4])
            dati.append(row[2])
            sensorid.append(row[5])
        close_connection(connection)
    except (Exception, psycopg2.Error) as error:
        print("Error while getting data", error)
    return laiks,dati,sensorid

laiks,dati,sensorid=read_database()
kkas={}
idx=0
for sensoraid in sensorid:
    if sensoraid in kkas.keys():
        kkas[sensoraid].append((dati[idx],laiks[idx]))
    else:
        kkas[sensoraid]=[]
        kkas[sensoraid].append((dati[idx],laiks[idx]))
    idx+=1

for key in kkas.keys():
    
    valuex=[]
    laiksx=[]
    #mainigaisvalue=''
    #mainigaislaiks=''
    for tupl in kkas['{}'.format(key)]:
        valuex.append(tupl[0])
        laiksx.append(tupl[1])

    fig_1=plt.figure(figsize=(10,6),dpi=100)
    axes_1 = fig_1.add_axes([0.05,0.15,0.9,0.8])
    axes_1.set_xlabel('Laiks')
    axes_1.set_ylabel('Datu vērtība')
    axes_1.set_title('Sensora grafiks: {}'.format(key))
    plt.xticks(rotation=90)#, ha='right')
    axes_1.plot(laiksx,valuex,label='Sensoraid: {}'.format(key))
    #axes_1.plot(x_1,y_2,label='2. serveru skapis')
    axes_1.legend(loc=0)
    plt.show()
