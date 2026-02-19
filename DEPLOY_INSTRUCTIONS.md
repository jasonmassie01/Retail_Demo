# Deployment Instructions (Argolis)

**Argolis Note**: Since you are deploying to an Argolis GCE instance, ensure you are either on the **Google VPN** (if using internal IPs) or have your **firewall** configured to allow SSH from your current IP.

1.  **Download** `deployment.zip` from this chat (or use the one in `retail_demo/`).
2.  **Transfer** to your GCE instance:
    ```bash
    # Replace <username> with your actual username on the instance
    # Replace <EXTERNAL_IP> with the instance's external IP (e.g., 104.154.153.150)
    scp deployment.zip <username>@<EXTERNAL_IP>:~/
    ```
3.  **SSH** into the instance:
    ```bash
    ssh <username>@<EXTERNAL_IP>
    ```
4.  **Run Deployment** (on the instance):
    ```bash
    unzip -o deployment.zip -d retail_demo
    cd retail_demo
    # Kill any existing streamlit process to free port 8501
    sudo pkill -f streamlit || true
    pip install -r requirements.txt
    nohup streamlit run app.py --server.port=8501 --server.address=0.0.0.0 > app.log 2>&1 &
    ```
5.  **Verify**:
    -   Check `app.log` for errors: `tail -f app.log`
    -   Access the app at `http://<EXTERNAL_IP>:8501`

**If you use `gcloud`**:
```bash
# Ensure you are authenticated
gcloud auth login

# SCP with gcloud (handles keys for you)
gcloud compute scp --zone=us-central1-a deployment.zip alloydb-instance:~/

# SSH and deploy
gcloud compute ssh --zone=us-central1-a alloydb-instance --command "unzip -o deployment.zip -d retail_demo && cd retail_demo && pip install -r requirements.txt && sudo pkill -f streamlit || true && nohup streamlit run app.py --server.port=8501 --server.address=0.0.0.0 > app.log 2>&1 &"
```
