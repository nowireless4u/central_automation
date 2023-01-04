# Aruba Central automation leveraging microservices with Netbox
Microservices to automate configuration and management of Aruba Central using Netbox as a source of truth.

# How It Works:

* Webhook receiver ingests messages from Aruba Central or Netbox. 
* Webhook receiver parses the received message to determine source and information. 
* Webhook receiver creates an alert based on information received and sends the alert via Redis stream to workers. 
* Workers listening to Redis stream recieve the alert and begin processing. 

# Assumptions

  1. Webhook configured properly.
     * Aruba Central (https://www.arubanetworks.com/techdocs/central/latest/content/nms/api/api_webhook.htm)
     * Netbox (https://demo.netbox.dev/static/docs/additional-features/webhooks/)
  2. Redis server configured properly.
  3. Azure Key Vault configured for RBAC.
  2. Firewall allowing port 5000 inbound.

# Install Instructions:

  1. Copy the files to host
  2. Create logs folder within central_automation folder.
  3. Modify example.env for your environment and save as .env.
  4. Modify creds/central.json for your environment. Note: This will be migrated to Azure Key Vault in the future.
  5. Create the following Azure Key Vault secrets.
     * central-(CustomerID)-webhooktoken
     * netbox-url
     * netbox-token
     * netbox-secret
     * redis-server
     * redis-password
  6. Issue docker compose up -d from the central_automation folder.
  
- - - -

The webhook receiver container leverages uvicorn web-server.

Question - Feel free to contact me:   
#(c) 2023 Jon Adams - JON@ADAMSLAB.NET
