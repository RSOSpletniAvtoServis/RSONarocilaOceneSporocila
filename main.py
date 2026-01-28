from typing import Union

from fastapi import FastAPI

from fastapi import HTTPException
import mysql.connector
from mysql.connector import pooling
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import re
import httpx
import os
import requests

adminbaza = os.getenv("ADMINBAZA", "RSOAdminVozila")
SERVICE_ADMVOZ_URL = os.getenv("SERVICE_ADMVOZ_URL","http://admvoz:8000")
SERVICE_UPOPRI_URL = os.getenv("SERVICE_UPOPRI_URL","http://upopri:8000")
SERVICE_POSZAP_URL = os.getenv("SERVICE_POSZAP_URL","http://poszap:8000")

def validate_identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", name):
        raise ValueError("Invalid database name")
    return name


app = FastAPI()

try:
    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        host="34.44.150.229",
        user="zan",
        password=">tnitm&+NqgoA=q6",
        database="RSOPoslovalnicaZaposleni",
        autocommit=True
    )
except Exception as e:
    print("Error: ",e)
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (dev only!)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Mikrostoritev": "NarocilaOceneSporocila"}

# Zacetek narocilo

class Narocilo(BaseModel):
    idtennant: str
    iduporabnik: str
    stsas: str
    idznamka: str
    idmodel: str
    idposlovalnica: str
    idstoritev: str
    idponudba: str
    datum: str
    ura: str
    uniqueid: str

@app.post("/dodajnarocilo/")
def dodaj_narocilo(narocilo: Narocilo):

    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT IDTennant, TennantDBNarocila FROM  " + adminbaza + ".TennantLookup WHERE IDTennant = %s"
        cursor.execute(query,(narocilo.idtennant,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="DB not found")
        tennantDB = row[1]
        
# start 

        stranka1 = dobiStranko(narocilo.iduporabnik,narocilo.uniqueid)
        if stranka1["Narocilo"] == "passed":
            idstranka = stranka1["IDStranka"]
            sql = "INSERT INTO "+tennantDB+".Narocilo(Cas,Datum,IDStranka,IDPoslovalnica,IDStoritev,StevilkaSasije,IDModel,IDZnamka,IDPonudba) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql,(narocilo.ura,narocilo.datum,idstranka,narocilo.idposlovalnica,narocilo.idstoritev,narocilo.stsas,narocilo.idmodel,narocilo.idznamka,narocilo.idponudba))
            # Fixed columns → no need to read cursor.description
            return {"Narocilo": "passed"}
        else:
            return stranka1

# end        
        
    except Exception as e:
        print("Error: ", e)
        return {"Narocilo": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Narocilo": "undefined"}


# Zacetek brisanja narocila

class Narocilo(BaseModel):
    idnarocilo: str
    idtennant: str
    uniqueid: str

@app.delete("/deletenarocilo/")
def brisi_narocilo(nar: Nar):

    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT IDTennant, TennantDBNarocila FROM  " + adminbaza + ".TennantLookup WHERE IDTennant = %s"
        cursor.execute(query,(narocilo.idtennant,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="DB not found")
        tennantDB = row[1]
        
# start 
        query = "SELECT IDNarocilo FROM  " + tennantDB + ".Narocilo WHERE IDNarocilo = %s AND Potrjen IS NULL"
        cursor.execute(query,(nar.idnarocilo,))
        row = cursor.fetchone()
        if row is None:
            return {"Narocilo": "failed", "Opis": "Narocilo, ki ga želite izbrisati je že potrjeno!!!"}
            raise HTTPException(status_code=404, detail="DB not found")

        sql = "DELETE FROM"+tennantDB+".Narocilo WHERE IDNarocilo = %s"
        cursor.execute(sql,(nar.idnarocilo))
        # Fixed columns → no need to read cursor.description
        return {"Narocilo": "passed"}

# end        
        
    except Exception as e:
        print("Error: ", e)
        return {"Narocilo": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Narocilo": "undefined"}

# Konec brisanja narocila


# Zacetek narocila

class Narocilo1(BaseModel):
    idtennant: str
    iduporabnik: str
    mode: str
    uniqueid: str


@app.post("/narocilastranka/")
def get_narocila(nar: Narocilo1):
    userid = nar.uniqueid
    nacin = ""
    if nar.mode == '1':
        nacin = " Zavrnjen IS NULL AND Zakljucen IS NULL AND Potrjen IS NULL"
    elif nar.mode == '2':
        nacin = " Zavrnjen IS NULL AND Potrjen = 1 AND Zakljucen IS NULL"
    elif nar.mode == '3':
        nacin = " Zavrnjen IS NULL AND Zakljucen = 1"
        
    try:
        with pool.get_connection() as conn:
            with conn.cursor() as cursor:
                # get tennant db
                query = "SELECT IDTennant, TennantDBNarocila FROM  " + adminbaza + ".TennantLookup WHERE IDTennant = %s"
                cursor.execute(query,(nar.idtennant,))
                row = cursor.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="DB not found")
                tennantDB = row[1]
                stranka1 = dobiStranko(nar.iduporabnik,nar.uniqueid)
                if stranka1["Narocilo"] == "passed":
                    idstranka = stranka1["IDStranka"]
                    
                    sql = "SELECT DISTINCT StevilkaSasije FROM "+ tennantDB +".Narocilo WHERE IDStranka = %s AND " + nacin
                    cursor.execute(sql,(idstranka,))
                    rows = cursor.fetchall()
                    sasije = list({ row[0] for row in rows if row[0] is not None })
                    print(sasije)
                    vozila = dobiVozila(sasije,nar.iduporabnik,nar.uniqueid)
                    
                    sql = "SELECT DISTINCT IDPoslovalnica FROM "+ tennantDB +".Narocilo WHERE IDStranka = %s AND " + nacin
                    cursor.execute(sql,(idstranka,))
                    rows = cursor.fetchall()
                    idpos = list({ row[0] for row in rows if row[0] is not None })
                    print(idpos)
                    poslovalnice = dobiPoslovalnice(idpos,nar.idtennant,nar.uniqueid)
                    print(poslovalnice)
                    
                    sql = "SELECT DISTINCT IDStoritev FROM "+ tennantDB +".Narocilo WHERE IDStranka = %s AND " + nacin
                    cursor.execute(sql,(idstranka,))
                    rows = cursor.fetchall()
                    idstor = list({ row[0] for row in rows if row[0] is not None })
                    print(idstor)
                    storitve = dobiStoritve(idstor,nar.uniqueid)
                    print(storitve)
                    
                    sql = "SELECT IDNarocilo, Cas, Datum, DatumZakljucka, IDStranka, IDPoslovalnica, IDStoritev, IDStatus, StevilkaSasije, IDModel, IDZnamka, IDPonudba FROM "+ tennantDB +".Narocilo WHERE IDStranka = %s AND " + nacin
                    cursor.execute(sql,(idstranka,))
                    rows = cursor.fetchall()
                    print(rows)
                    return [
                        {  
                            "IDNarocilo": row[0],
                            "Cas": row[1],
                            "Datum": row[2],
                            "DatumZakljucka": row[3],
                            "IDStranka": row[4],
                            "IDPoslovalnica": row[5],
                            "IDStoritev": row[6],
                            "IDStatus": row[7],
                            "StevilkaSasije": row[8],
                            "IDModel": row[9],
                            "IDZnamka": row[10],
                            "IDPonudba": row[11],
                            "NazivZnamke": vozila.get(row[8], {}).get("NazivZnamke", row[8]) or row[10],
                            "NazivModel": vozila.get(str(row[8]), {}).get("NazivModel", str(row[8])) or row[9],
                            "NazivPoslovalnice": poslovalnice.get(str(row[5]), {}).get("NazivPoslovalnice", str(row[5])) or row[5],
                            "NazivStoritve": storitve.get(str(row[6]), {}) or row[6]
                        } 
                            for row in rows ]

                
    except Exception as e:
        print("DB error:", e)
        #raise HTTPException(status_code=500, detail="Database error")
    return {"Narocilo": "failed"} 



# Konec narocila

def dobiStoritve(idstor,uniqueid):
    try:
        data = {"ids": idstor,"uniqueid": uniqueid}
        response = requests.post(f"{SERVICE_ADMVOZ_URL}/izbranestoritve/", json=data, timeout=5)
        #response.raise_for_status()  # Raise exception for HTTP errors  
        print(response)
        if "application/json" not in response.headers.get("Content-Type", ""):
            return {"Status": "failed"}
        else:
            result = response.json()
            print(result)
            return result
    except Exception as e:
        print("Prislo je do napake: ", e)
        return {"Status": "failed", "Error": e}
    return {"Status": "failed"}


def dobiPoslovalnice(idpos,idtennant,uniqueid):
    try:
        data = {"idpos": idpos, "idtennant": idtennant, "uniqueid": uniqueid}
        response = requests.post(f"{SERVICE_POSZAP_URL}/izbraneposlovalnice/", json=data, timeout=5)
        #response.raise_for_status()  # Raise exception for HTTP errors  
        print(response)
        if "application/json" not in response.headers.get("Content-Type", ""):
            return {"Status": "failed"}
        else:
            result = response.json()
            print(result)
            return result
    except Exception as e:
        print("Prislo je do napake: ", e)
        return {"Status": "failed", "Error": e}
    return {"Status": "failed"}
    


def dobiVozila(stsas,iduporabnik,uniqueid):
    try:
        data = {"stsas": stsas, "iduporabnik": iduporabnik, "uniqueid": uniqueid}
        response = requests.post(f"{SERVICE_ADMVOZ_URL}/izbranavozila/", json=data, timeout=5)
        #response.raise_for_status()  # Raise exception for HTTP errors  
        print(response)
        if "application/json" not in response.headers.get("Content-Type", ""):
            return {"Status": "failed"}
        else:
            result = response.json()
            print(result)
            return result
    except Exception as e:
        print("Prislo je do napake: ", e)
        return {"Status": "failed", "Error": e}
    return {"Status": "failed"}

def dobiStranko(iduporabnik,uniqueid):
    try:
        data = {"iduporabnik": iduporabnik, "uniqueid": uniqueid}
        response = requests.post(f"{SERVICE_UPOPRI_URL}/stranka/", json=data, timeout=5)
        #response.raise_for_status()  # Raise exception for HTTP errors  
        print(response)
        if "application/json" not in response.headers.get("Content-Type", ""):
            return {"Narocilo": "failed"}
        else:
            result = response.json()
            idstranka = result["IDStranka"]
            print(idstranka)
            print(result)
            return {"Narocilo": "passed", "IDStranka": idstranka}
    except Exception as e:
        print("Prislo je do napake: ", e)
        return {"Narocilo": "failed", "Error": e}
    return {"Narocilo": "failed"}
#Konec narocilo
    
