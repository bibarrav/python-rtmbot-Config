#Update Docker image and then re-create it                                      
                                                                                                        
#Update docker image, stop and  destroy existing container                                              
docker pull jgreeno/python-rtmbot                                                               
docker stop python-rtmbot                                                                                     
docker rm python-rtmbot                           

docker run --name python-rtmbot \
-e SLACK_TOKEN='xxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
-v /opt/python-rtmbot/plugins:/python-rtmbot/plugins \
--restart=always -d \
jgreeno/python-rtmbot