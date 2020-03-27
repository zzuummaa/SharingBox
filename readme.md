# SharingBox

### Описание WEB API

#### Users

* `/users POST`

Request example
```http request
POST /users HTTP/1.1
Host: 127.0.0.1:80
Content-Type: application/json

{"rfid_uid":"1234","user_name":"Вася"}
```

* `/users/<rfid_id> GET`

Request example
```http request
GET /users/1234 HTTP/1.1
Host: 127.0.0.1:80
```

* `/users/<rfid_id>/rents GET`

Request example
```http request
GET /users/1234/rents HTTP/1.1
Host: 127.0.0.1:80
```

#### Devices

* `/devices POST`

Request example
```http request
POST /devices HTTP/1.1
Host: 127.0.0.1:80
```

* `/devices/<device_id> GET`

Request example
```http request
GET /devices/1 HTTP/1.1
Host: 127.0.0.1:80
```

#### Equipments

* `/equipments POST`

Request example
```http request
POST /equipments HTTP/1.1
Host: 127.0.0.1:80
Content-Type: application/json

{"device_id":"1"}
```

* `/equipments/<equipment_id> GET`

Request example
```http request
GET /equipments/1 HTTP/1.1
Host: 127.0.0.1:80
```

* `/equipments/<equipment_id> PUT`

Request example
```http request
PUT /equipments/1 HTTP/1.1
Host: 127.0.0.1:80
Content-Type: application/json

{"device_id":"1"}
```

#### Rents

* `/rents POST` - начать аренду

Request example with `rfid_id`
```http request
POST /rents HTTP/1.1
Host: 127.0.0.1:80
Content-Type: application/json

{"rfid_id":"1234","equipment_id":"1"}
```

Request example with `user_id`
```http request
POST /rents HTTP/1.1
Host: 127.0.0.1:80
Content-Type: application/json

{"user_id":"1","equipment_id":"1"}
```

* `/rents/<rent_id> GET`

Request example
```http request
GET /rents/1 HTTP/1.1
Host: 127.0.0.1:80
```

* `/rents/<rent_id> PUT` - закончить аренду

Request example
```http request
PUT /rents/1 HTTP/1.1
Host: 127.0.0.1:80
```