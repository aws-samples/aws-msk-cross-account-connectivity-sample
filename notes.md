# Plan
Create 2 VPCs both with public subnets
- single subnet for client VPC
- 3 subnets for msk VPC
Create MSK cluster with plaintext and no auth
- Configure each broker with listening port 9094
- Configure each broker with unique advertised port 909X.
Create NLBs for each advertized port mapping to the one listening port 9094
Create single endpoint in client VPC pointing to 3 different NLBs