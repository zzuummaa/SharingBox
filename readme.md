# SharingBox

### Описание WEB API

#### Users
* `/users POST`
* `/users/<rfid_id> GET`
* `/users/<rfid_id>/equipments GET`

#### Devices
* `/devices POST`
* `/devices/<device_id> GET`

#### Equipments
* `/equipments POST`
* `/equipments/<equipment_id> GET`
* `/equipments/<equipment_id> PUT`

#### Rents
* `/rents POST` - начать аренду 
* `/rents/<rent_id> GET`
* `/rents/<rent_id> PUT` - закончить аренду