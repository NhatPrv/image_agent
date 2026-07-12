import requests
import time
import random

BASE = 'http://127.0.0.1:8000/api/v1'

def wait_server(timeout=30):
    for i in range(timeout):
        try:
            r = requests.get(f'{BASE}/system/info', timeout=3)
            if r.status_code == 200:
                print('Server is up')
                return True
        except Exception:
            pass
        time.sleep(1)
    print('Server did not become ready')
    return False

if not wait_server(30):
    raise SystemExit(1)

print('Triggering model scan...')
r = requests.post(f'{BASE}/models/scan')
print('scan response', r.status_code)

time.sleep(2)
models = requests.get(f'{BASE}/models').json()
print('Found models:', len(models))
if not models:
    raise SystemExit('No models found; put a checkpoint in models/ or use download manager')

model = models[0]
model_id = model.get('id')
print('Using model:', model.get('name'), model_id)

print('Requesting model load...')
r = requests.post(f'{BASE}/models/load', json={'model_id': model_id})
print('load request status', r.status_code)

# Poll for loaded model
loaded = False
for i in range(120):
    try:
        rr = requests.get(f'{BASE}/models/loaded', timeout=5)
        if rr.status_code == 200:
            data = rr.json()
            if data and data.get('id') == model_id:
                print('Model loaded')
                loaded = True
                break
    except Exception:
        pass
    time.sleep(1)
    print('waiting for model... ', i+1)

if not loaded:
    print('Model did not load within timeout; aborting generation test')
    raise SystemExit(2)

# Submit a light generation
payload = {
    'prompt': 'A simple test image, low detail',
    'negative_prompt': '',
    'width': 256,
    'height': 256,
    'steps': 10,
    'cfg_scale': 7.0,
    'seed': -1,
    'sampler': 'euler',
    'model_id': model_id,
    'type': 'txt2img',
    'priority': 'normal'
}
print('Submitting generation...')
r = requests.post(f'{BASE}/generations', json=payload)
print('generation submit status', r.status_code)
if not r.ok:
    print('submit failed', r.text)
    raise SystemExit(3)

gen = r.json()
gen_id = gen.get('id') or gen.get('generation_id') or gen.get('generationId')
print('Generation id', gen_id)

# Poll generation status
for i in range(600):
    try:
        gr = requests.get(f'{BASE}/generations/{gen_id}', timeout=10)
        if gr.ok:
            g = gr.json()
            status = g.get('status')
            print(f'[{i}] status={status}')
            if status in ('completed', 'failed'):
                print('Final generation status:', status)
                print(g)
                break
    except Exception as e:
        print('error polling', e)
    time.sleep(1)

print('Test finished')
