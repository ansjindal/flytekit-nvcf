#!/bin/bash

# Build the agent image
docker build -t nvcf-agent:latest -f Dockerfile.agent .

# Load the image into the sandbox
docker save nvcf-agent:latest > nvcf-agent.tar
flytectl sandbox exec -- docker load -i nvcf-agent.tar

# Create the agent configuration
cat << EOF > agent-config.yaml
agent:
  name: nvcf-agent
  image: nvcf-agent:latest
  port: 8000
  environment:
    - name: NVCF_API_KEY
      valueFrom:
        secretKeyRef:
          name: nvcf-secret
          key: NVCF_API_KEY
    - name: NVCF_ORG_NAME
      valueFrom:
        secretKeyRef:
          name: nvcf-secret
          key: NVCF_ORG_NAME
EOF

# Apply the agent configuration
flytectl sandbox exec -- kubectl apply -f agent-config.yaml

# Clean up
rm nvcf-agent.tar agent-config.yaml

echo "NVCF agent deployed successfully!"
