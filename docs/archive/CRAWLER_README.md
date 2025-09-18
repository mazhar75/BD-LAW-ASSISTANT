# 🏛️ BD Laws Crawler - Web UI System

## ✨ Features

### Scalable Web Interface
- **Custom Range Selection**: Choose any start and end act numbers (1-1303)
- **Language Support**: English and Bengali (বাংলা)
- **Real-time Monitoring**: Live progress updates and logs
- **Storage Statistics**: Track crawled acts and storage usage
- **Recent Activity**: View recently crawled acts

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install -r requirements_crawler.txt
```

### 2. Start Redis Server
```bash
redis-server --port 6380
```

### 3. Launch Web UI
```bash
python web_crawler_app.py
```

### 4. Open Browser
Navigate to: **http://localhost:5000**

## 📊 User Interface

### Control Panel
- **Starting Act**: Enter the first act number to crawl
- **Ending Act**: Enter the last act number to crawl
- **Language**: Select English or Bengali
- **Start/Stop Buttons**: Control the crawling process

### Live Monitoring
- **Status Display**: Current crawler state (Idle/Running/Completed)
- **Progress Bar**: Visual progress indicator
- **Statistics**: Real-time success/failure counts
- **Live Log**: Scrolling activity feed

### Storage Overview
- Total acts crawled
- Storage size in MB
- Language distribution (English/Bengali)
- Recently crawled acts list

## 🔧 Technical Details

### URL Format
```
English: http://bdlaws.minlaw.gov.bd/act-details-{number}.html
Bengali: http://bdlaws.minlaw.gov.bd/act-details-{number}.html?lang=bn
```

### Storage Structure
```
data/
└── raw/
    └── acts/
        ├── act_1.html.gz      # Compressed HTML
        ├── act_1.md.gz        # Compressed Markdown
        ├── act_1.meta.json    # Metadata
        └── ...
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI page |
| `/api/start` | POST | Start crawling with parameters |
| `/api/stop` | POST | Stop current crawling job |
| `/api/status` | GET | Get current crawler status |
| `/api/progress` | GET | Server-sent events for real-time updates |
| `/api/stats` | GET | Get storage statistics |
| `/api/recent` | GET | Get recently crawled acts |

## 📝 Usage Examples

### Crawl First 100 Acts (English)
1. Set Starting Act: `1`
2. Set Ending Act: `100`
3. Select Language: `English`
4. Click `Start Crawling`

### Crawl Acts 500-600 (Bengali)
1. Set Starting Act: `500`
2. Set Ending Act: `600`
3. Select Language: `বাংলা (Bengali)`
4. Click `Start Crawling`

### Crawl Specific Range
You can crawl any custom range, for example:
- Acts 1-10 for testing
- Acts 1000-1303 for the latest acts
- Single act by setting same start and end

## 🛠️ Configuration

### Rate Limiting
- Default: 2 seconds between requests
- Configurable in `web_crawler_app.py`

### Batch Processing
- Automatic pausing every 25 acts
- Prevents server overload

### Error Handling
- Automatic retry on failures
- Error logging in UI
- Graceful stop functionality

## 📊 Monitoring Features

### Real-time Updates
- Current act being processed
- Success/failure counters
- Progress percentage
- Estimated time remaining

### Storage Tracking
- Total files stored
- Storage size in MB
- Language distribution
- Recent activity feed

## 🔍 Data Quality

### Validation
- Content type verification
- Language detection
- Legal structure analysis
- Metadata completeness

### Compression
- HTML and Markdown files compressed with gzip
- ~70% storage savings
- Automatic decompression when reading

## 🚨 Important Notes

1. **Firecrawl API**: Ensure you have valid API credits
2. **Redis Server**: Must be running on port 6380
3. **Storage Space**: ~40MB for all 1303 acts
4. **Internet**: Stable connection required
5. **Rate Limiting**: Respects server limits (2s delay)

## 🎯 Use Cases

### Research
- Crawl specific act ranges for analysis
- Download Bengali versions for translation
- Build legal document datasets

### Development
- Test crawler with small ranges
- Monitor performance metrics
- Debug with live logging

### Production
- Scheduled crawling of new acts
- Incremental updates
- Multi-language support

## 📱 Browser Support

- Chrome/Edge (Recommended)
- Firefox
- Safari
- Mobile browsers supported

## 🐛 Troubleshooting

### Server Won't Start
- Check Redis is running: `redis-cli -p 6380 ping`
- Verify port 5000 is available
- Check Python dependencies installed

### Crawling Fails
- Verify Firecrawl API key in `.env`
- Check internet connection
- Review error logs in UI

### No Data Retrieved
- Verify URL format is correct
- Check act numbers are valid (1-1303)
- Ensure language parameter is set

## 📈 Performance

- **Speed**: ~15 seconds per act (with rate limiting)
- **Success Rate**: Typically >95%
- **Memory Usage**: <200MB
- **Concurrent Support**: Single job at a time

## 🔄 Future Enhancements

- [ ] Multiple concurrent jobs
- [ ] Scheduled crawling
- [ ] Export functionality
- [ ] Advanced filtering
- [ ] API rate limit visualization
- [ ] Dark mode theme

## 📄 License

This crawler is for educational and research purposes. Please respect the website's terms of service and rate limits.

---

**Built with**: Flask, Firecrawl, Redis, Python
**UI Framework**: Pure HTML/CSS/JavaScript
**Storage**: Compressed file system with metadata