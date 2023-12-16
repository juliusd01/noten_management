# Web Service Notenmanagement

## Connect to virtual machine
```sh
ssh -i /path/to/private_key debian@185.128.118.134
```

## Pulling docker image from dockerhub
```sh
sudo docker login
```
```sh
sudo docker pull juliusdoebelt01/noten_manager:latest
```

## Run Docker container on port 80
```sh
sudo docker run -p 80:5000 juliusdoebelt01/noten_manager:latest
```

## Use existing software
Go to http://185.128.118.134:8080 and experiment with it (only until 03/2024).