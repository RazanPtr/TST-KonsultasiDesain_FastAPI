from fastapi import FastAPI, HTTPException, Depends, status, APIRouter, Request
from fastapi.encoders import jsonable_encoder
import json
from pydantic import BaseModel
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt

class Item(BaseModel):
	id: int
	name: str
	deskripsi: str
	tanggalpesan: str
	status: str

class Permintaan(BaseModel):
    id: int
    id_desainer: int

class Konsul(BaseModel):
	id_desainer: int
	nama: str
	nohp: int

class User:
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)

json_filename="desain.json"

with open(json_filename, "r") as read_file:
    data = json.load(read_file)

def write_data(data):
    with open(json_filename, "w") as write_file:
        json.dump(data, write_file, indent=4)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
app = FastAPI()
JWT_SECRET = 'myjwtsecret'
ALGORITHM = 'HS256'

desain = APIRouter(tags=["Desain"], )
konsuldesain = APIRouter(tags=["Konsul Desain"])
alldesain = APIRouter(tags=["All Data"])
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
async def create_user(username: str, password: str):
    last_user_id = data['user'][-1]['id'] if data['user'] else 0
    user_id = last_user_id + 1
    user = jsonable_encoder(User(id=user_id, username=username, password_hash=bcrypt.hash(password)))
    data['user'].append(user)
    write_data(data)
    return {'message': 'User created successfully'}

@authentication.get('/users/me')
async def get_user(user: User = Depends(get_current_user)):
    return {'id': user.id, 'username': user.username, 'role': 'admin'}

@desain.get('/desain')
async def read_desain(user: User = Depends(get_current_user)):
	return data['desain']

@desain.get('/desain/{status}')
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
async def read_all(user: User = Depends(get_current_user)):
    merged_data_list = []

    for desain_item in data['desain']:
        for desain_permintaan in data['permintaan']:
            for desain_desainer in data['konsuldesain']:
                if (desain_item['id'] == desain_permintaan['id'] and
                    desain_permintaan['id_desainer'] == desain_desainer['id_desainer']):
                    merged_data = {
                        'name': desain_item['name'],
                        'desc': desain_item['deskripsi'],
                        'tanggalpesan': desain_item['tanggalpesan'],
                        'status': desain_item['status'],
                        'nama_desainer': desain_desainer['nama'],
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
async def add_items(items: dict, user: User = Depends(get_current_user)):
    konsul_dict = items.get('konsuldesain', {})
    item_dict = items.get('desain', {})
    permintaan_dict = items.get('permintaan', {})

    # Mendapatkan ID terakhir untuk masing-masing tabel
    last_desain_id = data['desain'][-1]['id'] if data['desain'] else 0
    last_permintaan_id = data['permintaan'][-1]['id'] if data['permintaan'] else 0
    last_konsuldesain_id = data['konsuldesain'][-1]['id_desainer'] if data['konsuldesain'] else 0
    last_permintaan_id_desainer = data['permintaan'][-1]['id_desainer'] if data['permintaan'] else 0

    # Memastikan bahwa ID pada tabel desain dan tabel permintaan adalah sama
    item_dict["id"] = last_desain_id + 1
    permintaan_dict["id"] = last_permintaan_id + 1
    konsul_dict["id_desainer"] = last_konsuldesain_id + 1
    permintaan_dict["id_desainer"] = last_permintaan_id_desainer + 1

    for desain_item in data['konsuldesain']:
        if desain_item['id_desainer'] == konsul_dict['id_desainer']:
            raise HTTPException(
                status_code=400, detail=f'Desain ID {konsul_dict["id_desainer"]} already exists'
            )

    for desain_item in data['desain']:
        if desain_item['id'] == item_dict['id']:
            raise HTTPException(
                status_code=400, detail=f'Desain ID {item_dict["id"]} already exists'
            )
			
    data['permintaan'].append({
        "id": permintaan_dict["id"],
        "id_desainer": permintaan_dict["id_desainer"]
    })

    data['konsuldesain'].append(konsul_dict)

    data['desain'].append(item_dict)

    write_data(data)

    return "Add data successfully"

@desain.put('/desain/{item_id}')
async def update_desain(item_id: int, item: Item, user: User = Depends(get_current_user)):
    item_dict = item.dict()
    item_found = False
    
    for desain_idx, desain_item in enumerate(data['desain']):
        if desain_item['id'] == item_id:
            item_found = True
            data['desain'][desain_idx] = {
                "name": item_dict["name"],
                "deskripsi": item_dict["deskripsi"],
                "tanggalpesan": item_dict["tanggalpesan"],
                "status": item_dict["status"],
                "id": item_id
            }
            
            with open(json_filename, "w") as write_file:
                json.dump(data, write_file, indent=4)
            
            return "updated"
    
    if not item_found:
        return "desain ID not found."
    
    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

@konsuldesain.put('/konsuldesain/{item_id}')
async def update_desain(item_id: int, item: Konsul, user: User = Depends(get_current_user)):
    item_dict = item.dict()
    item_found = False
    
    for desain_idx, desain_item in enumerate(data['konsuldesain']):
        if desain_item['id_desainer'] == item_id:
            item_found = True
            data['konsuldesain'][desain_idx] = {
                "nama": item_dict["nama"],
                "nohp": item_dict["nohp"],
                "id_desainer": item_id
            }
            
            with open(json_filename, "w") as write_file:
                json.dump(data, write_file, indent=4)
            
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
            
            with open(json_filename,"w") as write_file:
                json.dump(data, write_file, indent=4)
            
            return "deleted"
    
    if not item_found:
        return "desain ID not found."
    
    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

@konsuldesain.put('/konsuldesain/{item_id}')
async def update_konsuldesain(item_id: int, item: Konsul, user: User = Depends(get_current_user)):
    item_dict = item.dict()
    item_found = False
    
    for desain_idx, desain_item in enumerate(data['konsuldesain']):
        if desain_item['id_desainer'] == item_id:
            item_found = True
            data['konsuldesain'][desain_idx] = {
                "nama": item_dict["nama"],
                "nohp": item_dict["nohp"],
                "id_desainer": item_id
            }
            
            with open(json_filename, "w") as write_file:
                json.dump(data, write_file, indent=4)
            
            return "deleted"
    
    if not item_found:
        return "desain ID not found."
    
    raise HTTPException(
        status_code=404, detail=f'item not found'
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

app.include_router(authentication)
app.include_router(desain)
app.include_router(konsuldesain)
app.include_router(alldesain)