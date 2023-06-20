# The three ways to deploy a model

## Experiment Tracking

- Design
- Train
- Operate

training pipeline >> model >> deployment

## Deployment

Q: Can the model wait for a while or does it need to start delivering predictions right away? 

If the answer is yes, then the answer is to use Batch deployment. In this case the model is not online constantly, batches of data are applied to it periodically. 

If the naswer is no, then the answer is to use Streaming deployment. In this case the model is online asap and is continuously online. Data is ontantly being applied to it. 


### Batch Mode

The model runs regularly on a schedule. 

DB/DL >> model >> DWH >> BI Dashboard

### Web service

The model is triggered by client requests.

user >> app >> backend >> model >> backend >> app >> user

### Streaming 

The model is always online and constantly processing data. 

user >> service >> message queue >> model >> message queue >> descision system  