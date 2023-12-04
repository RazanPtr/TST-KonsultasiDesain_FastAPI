from fastapi import FastAPI, HTTPException, Depends, status, APIRouter, Request, Form
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import json
from pydantic import BaseModel
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from typing import List
from reqpsyco import get_psychologist_list, get_user_list
from pymongo import MongoClient

client = MongoClient("mongodb+srv://18221132:123@tstdesain.olxinss.mongodb.net/?retryWrites=true&w=majority")
db = client['IntegrasiDesain']
collection = db['desain']

data = collection.find_one()

def write_data(data):
    collection.replace_one({}, data, upsert=True)

# class Item(BaseModel):
# 	id: int
# 	desainname: str
# 	deskripsi: str
# 	tanggalpesan: str
# 	status: str

# class Permintaan(BaseModel):
#     id: int
#     id_desainer: int

# class Konsul(BaseModel):
# 	id_desainer: int
# 	namadesainer: str
# 	nohp: int

class User:
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
app = FastAPI()
JWT_SECRET = 'myjwtsecret'
ALGORITHM = 'HS256'

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

psychology = APIRouter(tags=["Psikologis"])
desain = APIRouter(tags=["Desain"], )
konsuldesain = APIRouter(tags=["Konsul Desain"])
alldesain = APIRouter(tags=["All Desain Data"])
authentication = APIRouter(tags=["Authentication"])

def get_user_by_username(username):
    for desain_user in data['user']:
        if desain_user['username'] == username:
            return desain_user
    return None

def authenticate_user(username: str, password: str):
    user_data = get_user_by_username(username)
    if not user_data:
        return None

    user = User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])

    if not user.verify_password(password):
        return None

    return user

@authentication.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        print(f"Invalid username or password for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )

    token = jwt.encode({'id': user.id, 'username': user.username}, JWT_SECRET, algorithm=ALGORITHM)

    return {'access_token': token, 'token_type': 'bearer'}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = get_user_by_username(payload.get('username'))
        return User(id=user['id'], username=user['username'], password_hash=user['password_hash'])
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid username or password'
        )

@authentication.post('/users')
async def create_user(username: str = Form(...), password: str = Form(...)):
    last_user_id = data['user'][-1]['id'] if data['user'] else 0
    user_id = last_user_id + 1
    user = User(id=user_id, username=username, password_hash=bcrypt.hash(password))
    data['user'].append(jsonable_encoder(user))
    write_data(data)
    return {'message': 'User created successfully'}

@authentication.get('/users/me')
async def get_user(user: User = Depends(get_current_user)):
    return {'id': user.id, 'username': user.username, 'role': 'admin'}

@desain.get('/desain')
async def read_desain(user: User = Depends(get_current_user)):
	return data['desain']

@desain.get('/desain/{status}', description="under review, on progress, completed")
async def read_desain_status(status: str, user: User = Depends(get_current_user)):
	list_status = []
	for desain_status in data['desain']:
		if desain_status['status'] == status:
			list_status.append(desain_status)
	return list_status
	raise HTTPException(
		status_code=404, detail=f'desain not found'
	)

@konsuldesain.get('/konsuldesain')
async def read_konsuldesain(user: User = Depends(get_current_user)):
	return data['konsuldesain']

@alldesain.get('/alldata')
async def read_all_desain_data(user: User = Depends(get_current_user)):
    merged_data_list = []

    for desain_item in data['desain']:
        for desain_permintaan in data['permintaan']:
            for desain_desainer in data['konsuldesain']:
                if (desain_item['id'] == desain_permintaan['id'] and
                    desain_permintaan['id_desainer'] == desain_desainer['id_desainer']):
                    merged_data = {
                        'desainname': desain_item['desainname'],
                        'tanggalpesan': desain_item['tanggalpesan'],
                        'status': desain_item['status'],
                        'nama_desainer': desain_desainer['namadesainer'],
                        'nohp': desain_desainer['nohp']
                    }
                    merged_data_list.append(merged_data)
                    
    if not merged_data_list:
        raise HTTPException(
            status_code=404, detail=f'desain not found'
        )

    return merged_data_list

@konsuldesain.get('/konsuldesain/{item_id}')
async def read_konsuldesain(item_id: int, user: User = Depends(get_current_user)):
	for desain_item in data['konsuldesain']:
		if desain_item['id_desainer'] == item_id:
			return desain_item
	raise HTTPException(
		status_code=404, detail=f'desainer not found'
	)

@alldesain.post('/alldata')
async def add_desain_items(
    desainname: str = Form(...),
    tanggalpesan: str = Form(...),
    status: str = Form(...),
    namadesainer: str = Form(...),
    nohp: int = Form(...),
    user: User = Depends(get_current_user)
):
    # Mendapatkan ID terakhir untuk masing-masing tabel
    last_desain_id = data['desain'][-1]['id'] if data['desain'] else 0
    last_permintaan_id = data['permintaan'][-1]['id'] if data['permintaan'] else 0
    last_konsuldesain_id = data['konsuldesain'][-1]['id_desainer'] if data['konsuldesain'] else 0
    last_permintaan_id_desainer = data['permintaan'][-1]['id_desainer'] if data['permintaan'] else 0

    # Memastikan bahwa ID pada tabel desain dan tabel permintaan adalah sama
    desain_id = last_desain_id + 1
    permintaan_id = last_permintaan_id + 1
    konsuldesain_id = last_konsuldesain_id + 1
    permintaan_id_desainer = last_permintaan_id_desainer + 1

    # Memastikan ID belum digunakan
    for desain_item in data['konsuldesain']:
        if desain_item['id_desainer'] == konsuldesain_id:
            raise HTTPException(
                status_code=400, detail=f'Desain ID {konsuldesain_id} already exists'
            )

    for desain_item in data['desain']:
        if desain_item['id'] == desain_id:
            raise HTTPException(
                status_code=400, detail=f'Desain ID {desain_id} already exists'
            )

    # Menambahkan data ke masing-masing tabel
    data['permintaan'].append({
        "id": permintaan_id,
        "id_desainer": permintaan_id_desainer
    })

    data['konsuldesain'].append({
        "namadesainer": namadesainer,
        "nohp": nohp,
        "id_desainer": konsuldesain_id
    })

    data['desain'].append({
        "desainname": desainname,
        "tanggalpesan": tanggalpesan,
        "status": status,
        "id": desain_id
    })

    # Menyimpan data ke file
    write_data(data)

    return "Add data successfully"

@desain.put('/desain/{item_id}')
async def update_desain(
    item_id: int,
    desainname: str = Form(...),
    tanggalpesan: str = Form(...),
    status: str = Form(...),
    user: User = Depends(get_current_user)
):
    item_found = False
    
    for desain_idx, desain_item in enumerate(data['desain']):
        if desain_item['id'] == item_id:
            item_found = True
            data['desain'][desain_idx] = {
                "name": desainname,
                "tanggalpesan": tanggalpesan,
                "status": status,
                "id": item_id
            }
            
            write_data(data)
            
            return "updated"
    
    if not item_found:
        return "desain ID not found."
    
    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

@konsuldesain.put('/konsuldesain/{item_id}')
async def update_konsuldesain(
    item_id: int,
    namadesainer: str = Form(...),
    nohp: int = Form(...),
    user: User = Depends(get_current_user)
):
    item_found = False
    
    for desain_idx, desain_item in enumerate(data['konsuldesain']):
        if desain_item['id_desainer'] == item_id:
            item_found = True
            data['konsuldesain'][desain_idx] = {
                "namadesainer": namadesainer,
                "nohp": nohp,
                "id_desainer": item_id
            }
            
            write_data(data)
            
            return "updated"
    
    if not item_found:
        return "konsuldesain ID not found."
    
    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

@alldesain.delete('/alldata/{item_id}')
async def delete_desain(item_id: int, user: User = Depends(get_current_user)):
    item_found = False
    
    # Inisialisasi list untuk menyimpan foreign keys
    foreign_keys_to_delete = []
    
    for desain_idx, desain_item in enumerate(data['desain']):
        if desain_item['id'] == item_id:
            item_found = True
            
            # Simpan ID dari desain yang akan dihapus
            desain_id_to_delete = desain_item['id']
            
            # Cari foreign keys terkait
            for permintaan_item in data['permintaan']:
                if permintaan_item['id_desainer'] == desain_id_to_delete:
                    foreign_keys_to_delete.append(permintaan_item)
            for konsuldesain_item in data['konsuldesain']:
                if konsuldesain_item['id_desainer'] == desain_id_to_delete:
                    foreign_keys_to_delete.append(konsuldesain_item)
            
            # Hapus desain dari data
            data['desain'].pop(desain_idx)
            
            # Hapus foreign keys terkait
            for foreign_key in foreign_keys_to_delete:
                if foreign_key in data['permintaan']:
                    data['permintaan'].remove(foreign_key)
                if foreign_key in data['konsuldesain']:
                    data['konsuldesain'].remove(foreign_key)
            
            write_data(data)
            
            return "deleted"
    
    if not item_found:
        return "desain ID not found."
    
    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

@desain.patch('/desain/{item_id}')
async def patch_desain(item_id: int, fields_to_update: List[dict], user: User = Depends(get_current_user)):
    item_found = False

    for desain_idx, desain_item in enumerate(data['desain']):
        if desain_item['id'] == item_id:
            item_found = True

            # Perbarui nilai-nilai yang diberikan dalam fields_to_update
            for field_update in fields_to_update:
                field_name = field_update.get('field')
                new_value = field_update.get('value')
                if field_name and field_name in desain_item:
                    desain_item[field_name] = new_value

            write_data(data)

            return "updated"

    if not item_found:
        return "desain ID not found."

    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

@konsuldesain.patch('/konsuldesain/{item_id}')
async def patch_desain(item_id: int, fields_to_update: List[dict], user: User = Depends(get_current_user)):
    item_found = False

    for desain_idx, desain_item in enumerate(data['konsuldesain']):
        if desain_item['id_desainer'] == item_id:
            item_found = True

            # Perbarui nilai-nilai yang diberikan dalam fields_to_update
            for field_update in fields_to_update:
                field_name = field_update.get('field')
                new_value = field_update.get('value')
                if field_name and field_name in desain_item:
                    desain_item[field_name] = new_value

            write_data(data)

            return "updated"

    if not item_found:
        return "desain ID not found."

    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

@psychology.get('/Psychologist/{specialty}', description="Depression and Anxiety, Family Conflict Resolution, Child and Adolescent Counseling ,Substance Abuse and Addiction, Marriage and Couples Counseling, Stress Management, Anxiety Disorders")
async def get_psychologist_specialty(specialty: str ,User = Depends(get_current_user)):
    psyc = []
    for psy in get_psychologist_list():
        if psy['specialty'] == specialty:
            psyc.append(psy)
    return psyc

@psychology.get('/MatchUserAvailability', description="Match the user and psychologist availability to get consultation")
async def match_user_availability(name: str,User = Depends(get_current_user)):
    psychologist = []
    try:
        for psy in get_user_list():
            if psy['username'] == name:
                for psyc in get_psychologist_list():
                        if psy['day'] == psyc['availability']:
                            psychologist.append(psyc)
                        else:
                            pass
                if len(psychologist) == 0:
                    return 'Not available day for the moment'
                else:
                    return psychologist
    except:
        return 'User '+name+' not found'

@psychology.get('/DesainRecommendation', description="We provide design recommendation based on user psychology preference")
async def get_desain_recommendation(user_psychology_name: str, User = Depends(get_current_user)):
    try:
        for user in get_user_list():
            if user['username'] == user_psychology_name:
                for desain in data['detail']:
                    if user['preference'] == desain['preferensi']:
                        return desain
                    elif user['preference'] == "-":
                        return "user doesn't have psychology preference"
    except:
        return 'User '+user_psychology_name+' not found'

@psychology.get('/UserPsychology', description="First three user is an admin, they don't have any psychology preference")
async def get_psychologist_user():
    user_list=[]
    for user in get_user_list():
        user_list.append({k: user[k] for k in ('username', 'email', 'date_of_birth', 'day', 'tags')})
    return user_list

app.include_router(authentication)
app.include_router(desain)
app.include_router(konsuldesain)
app.include_router(alldesain)
app.include_router(psychology)