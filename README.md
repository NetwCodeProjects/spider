# How to Run It
```pip install scrapy```

```powershell
python run.py \
  --url https://nanoscience.oxinst.com \
  --filter-url /assets/uploads/ \
  --download \
  --max-pages 300 \
  --export html \
  --pattern Optistat \
  --content
```
