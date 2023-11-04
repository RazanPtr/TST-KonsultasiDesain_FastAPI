from fastapi import FastAPI, HTTPException
import json
from pydantic import BaseModel


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

json_filename="desain.json"

with open(json_filename,"r") as read_file:
	data = json.load(read_file)

def write_data(data):
    with open(json_filename, "w") as write_file:
        json.dump(data, write_file, indent=4)

app = FastAPI()

@app.get('/desain')
async def read_desain():
	return data['desain']

@app.get('/desain/{status}')
async def read_desain_status(status: str):
	list_status = []
	for desain_status in data['desain']:
		if desain_status['status'] == status:
			list_status.append(desain_status)
	return list_status
	raise HTTPException(
		status_code=404, detail=f'desain not found'
	)

@app.get('/konsuldesain')
async def read_konsuldesain():
	return data['konsuldesain']

@app.get('/')
async def read_all():
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

@app.get('/desain/{item_id}')
async def read_desain(item_id: int):
	for desain_item in data['desain']:
		if desain_item['id'] == item_id:
			return desain_item
	raise HTTPException(
		status_code=404, detail=f'desain not found'
	)

@app.get('/konsuldesain/{item_id}')
async def read_konsuldesain(item_id: int):
	for desain_item in data['konsuldesain']:
		if desain_item['id_desainer'] == item_id:
			return desain_item
	raise HTTPException(
		status_code=404, detail=f'desainer not found'
	)

# @app.post('/desain')
# async def add_desain(item: Item):
#     item_dict = item.dict()

#     # Cek apakah ID sudah ada
#     for desain_item in data['desain']:
#         if desain_item['id'] == item_dict['id']:
#             raise HTTPException(
#                 status_code=400, detail=f'Desain ID {item_dict["id"]} already exists'
#             )

#     # Jika ID belum ada, tambahkan desain baru
#     data['desain'].append({
#         "id": item_dict["id"],
#         "name": item_dict["name"],
#         "deskripsi": item_dict["deskripsi"],
#         "tanggalpesan": item_dict["tanggalpesan"],
#         "status": item_dict["status"]
#     })

#     write_data(data)

#     return item_dict

# @app.post('/konsuldesain')
# async def add_desain(konsul: Konsul):
#     konsul_dict = konsul.dict()

#     # Cek apakah ID sudah ada
#     for desain_item in data['konsuldesain']:
#         if desain_item['id_desainer'] == konsul_dict['id_desainer']:
#             raise HTTPException(
#                 status_code=400, detail=f'Desain ID {konsul_dict["id_desainer"]} already exists'
#             )

#     # Jika ID belum ada, tambahkan desain baru
#     data['konsuldesain'].append({
#         "id_desainer": konsul_dict["id_desainer"],
#         "nama": konsul_dict["nama"],
#         "nohp": konsul_dict["nohp"]
#     })

#     write_data(data)

#     return konsul_dict

@app.post('/')
async def add_items(items: dict):
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

@app.put('/desain')
async def update_desain(item: Item):
	item_dict = item.dict()
	item_found = False
	for desain_idx, desain_item in enumerate(data['desain']):
		if desain_item['id'] == item_dict['id']:
			item_found = True
			data['desain'].append({
				"id": item_dict["id"],
				"name": item_dict["name"],
				"deskripsi": item_dict["deskripsi"],
				"tanggalpesan": item_dict["tanggalpesan"],
				"status": item_dict["status"]
			})
			
			with open(json_filename,"w") as write_file:
				json.dump(data, write_file, indent=4)
			return "updated"
	
	if not item_found:
		return "desain ID not found."
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

# @app.delete('/desain/{item_id}')
# async def delete_desain(item_id: int):

# 	item_found = False
# 	for desain_idx, desain_item in enumerate(data['desain']):
# 		if desain_item['id'] == item_id:
# 			item_found = True
# 			data['desain'].pop(desain_idx)
			
# 			with open(json_filename,"w") as write_file:
# 				json.dump(data, write_file)
# 			return "updated"
	
# 	if not item_found:
# 		return "desain ID not found."
# 	raise HTTPException(
# 		status_code=404, detail=f'item not found'
# 	)

@app.delete('/desain/{item_id}')
async def delete_desain(item_id: int):
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
            
            return "updated"
    
    if not item_found:
        return "desain ID not found."
    
    raise HTTPException(
        status_code=404, detail=f'item not found'
    )
