from typing import Union

from fastapi import FastAPI

import mysql.connector

app = FastAPI()


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
        
        query = "SELECT IDTennant, TennantDBPoslovalnice FROM  " + adminbaza + ".TennantLookup WHERE IDTennant = %s"
        cursor.execute(query,(narocilo.idtennant,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="DB not found")
        tennantDB = row[1]
        
# start 

        try:
            data = {"ids": vodja_ids, "uniqueid": vodja.uniqueid}
            response = requests.post(f"{SERVICE_UPOPRI_URL}/usernames/", json=data, timeout=5)
            #response.raise_for_status()  # Raise exception for HTTP errors  
            print(response)
            if "application/json" not in response.headers.get("Content-Type", ""):
                return {"Narocilo": "failed"}
            else:
                result = response.json()
                print(result)
                return {"Narocilo": "failed"}     
                cursor.execute("SELECT IDTennant, NazivTennanta, TennantDBNarocila, TennantDBPoslovalnice, IDVodja FROM TennantLookup")
                rows = cursor.fetchall()
                # Fixed columns → no need to read cursor.description
                return [
                    {"IDTennant": row[0], "NazivTennanta": row[1], "TennantDBNarocila": row[2], "TennantDBPoslovalnice": row[3], "IDVodja": row[4], "username": result.get(str(row[4]))}
                    for row in rows
                ]
        except Exception as e:
            print("Prislo je do napake: ", e)
            return {"Narocilo": "failed"}

# end        
        
        sql = "INSERT INTO Uporabnik(UporabniskoIme,Geslo,Vloga,UniqueID,IDTennant) VALUES (%s,%s,%s,%s,%s)"
        cursor.execute(sql, (zaposleni.username,hash,2,timestamp,zaposleni.idtennant))
        
        query = "SELECT IDUporabnik, UporabniskoIme, Vloga, UniqueID FROM Uporabnik WHERE UporabniskoIme = %s"
        cursor.execute(query,(zaposleni.username,))
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Znamka not found")

        return {"Narocilo": "passed"}

        
        
        
    except Exception as e:
        print("Error: ", e)
        return {"Narocilo": "failed", "Error": e}
    finally:
        cursor.close()
        conn.close()  
    return {"Narocilo": "undefined"}


#Konec narocilo
    
