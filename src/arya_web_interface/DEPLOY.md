# Deployment Instructions

## Option 1: Copy Built Files (Recommended)

### On your local machine:

1. Copy the `dist/` folder contents to the robot:

```bash
# Using scp with password prompt
scp -r dist/* arya@192.168.1.101:/home/arya/amr_ws/src/arya_web_interface/arya_web_interface/static/

# Or copy the entire folder
scp -r dist arya@192.168.1.101:/home/arya/amr_ws/src/arya_web_interface/arya_web_interface/
```

2. The files should be placed in the static folder where FastAPI serves them:
```
/home/arya/amr_ws/src/arya_web_interface/arya_web_interface/static/
```

## Option 2: Development Mode (Hot Reload)

For development with hot reload, you can run Vite dev server:

```bash
cd src/arya_web_interface
npm install
npm run dev
```

Then access at `http://localhost:3000`

**Note:** Update `vite.config.ts` to point to your robot's IP:
```javascript
server: {
  port: 3000,
  proxy: {
    '/ws': {
      target: 'ws://192.168.1.101:8000',  // Your robot IP
      ws: true,
    },
    '/api': {
      target: 'http://192.168.1.101:8000',
      changeOrigin: true,
    },
  },
},
```

## Option 3: Full Production Deploy

On the robot:

```bash
cd ~/amr_ws/src/arya_web_interface

# Build the React app
npm install
npm run build

# The dist/ folder will be created with static files
# FastAPI will serve these automatically
```

## Verifying Deployment

1. Start the FastAPI server on the robot:
```bash
cd ~/amr_ws
python3 src/arya_web_interface/arya_web_interface/web_node.py
```

2. Open browser and navigate to:
```
http://<robot-ip>:8000
```

Or if using a different port, check the web_node.py configuration.

## Files Structure After Deployment

```
~/amr_ws/src/arya_web_interface/arya_web_interface/
├── web_node.py              # FastAPI server
├── static/
│   ├── index.html          # Main entry point
│   ├── assets/
│   │   ├── index-*.js     # Bundled JS
│   │   └── index-*.css     # Bundled CSS
```

## Troubleshooting

### WebSocket Connection Issues
- Ensure the robot's firewall allows port 8000
- Check WebSocket URL in browser console (F12)
- Verify web_node.py is running on the robot

### Static Files Not Loading
- Check FastAPI is configured to serve static files
- Verify path in web_node.py matches static folder location
