# max_schedule_bot

Max bot for viewing educational institution class schedules. Allows students and teachers to easily get up-to-date schedules.

## Features

### For Students
- View group schedule
- Navigation through days and weeks
- Search schedule by group number

### For Teachers
- View personal schedule
- Search by last name and initials
- Convenient day navigation

### Technical Features
- Automatic week type detection (numerator/denominator)
- Weekend day checking
- Action and error logging
- Convenient inline buttons for navigation

## Installation
Clone the repository

```bash
git clone https://github.com/moonPrTea/max_schedule_bot.git
cd max_schedule_bot
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Running the Bot
```bash
python3 main.py
```

## Project Structure
```
max_schedule_bot/
├── models/          # database models
├── handlers/        # bot handlers
├── dependencies/    # database dependencies
├── helpers.py/       # states, loger and helper functions 
├── settings.py      # environment settings
└── main.py          # main application
```