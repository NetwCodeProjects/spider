# How to Run It
```pip install scrapy```

```powershell
python run.py \
  --url https://google.com \
  --filter-url /assets/uploads/ \
  --download \
  --max-pages 300 \
  --export xml json csv html(default) \
  --pattern Optistat \
  --content
```
