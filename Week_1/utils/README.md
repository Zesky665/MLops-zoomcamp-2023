## Generate keys
RUN
`ssh-keygen -t rsa -b 4096 -m pem -f mlops_kp && openssl rsa -in mlops_kp -outform pem && mv mlops_kp mlops_kp.pem && chmod 400 mlops_kp.pem`