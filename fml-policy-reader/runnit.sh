pip install -r requirements.txt

# Check if chromedriver exists in the current directory
if [ ! -f "./chromedriver" ]; then
  echo "Error: chromedriver not found in the current directory.  Install it first..."
  exit 1
fi

python search_crawl.py