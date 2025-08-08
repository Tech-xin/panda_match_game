# Panda Match

Panda Match is a web-based match-3 puzzle game built using Django. Players match three identical blocks to clear them from the board, aiming to complete levels within a limited number of moves.

## Features

- **Simple Gameplay**: Match three identical blocks to clear them from the board
- **User Authentication**: Register, login, logout, password reset, and profile management
- **Game Progress**: Save your progress and continue where you left off
- **Leaderboard System**: Compete with other players on daily, weekly, and all-time leaderboards
- **Responsive Design**: Play on both desktop and mobile devices

## Game Mechanics

- **Match-3 Logic**: Select three identical blocks to remove them from the board
- **Special Items**: Use reshuffle, withdraw, and add buffer to help you progress
- **Level Progression**: Complete levels to unlock new challenges with increasing difficulty
- **Scoring System**: Earn points based on completed matches and level difficulty

## Technology Stack

- **Backend**: Django (Python web framework)
- **Database**: SQLite (default), with support for PostgreSQL in production
- **Frontend**: HTML, CSS (Bootstrap), JavaScript, jQuery
- **Authentication**: Django's built-in authentication system
- **Responsive Design**: Bootstrap for mobile-friendly UI

## Screenshots

![Login Screen](screenshots/login.png)

![Game Board](screenshots/gameplay.png)

![Leaderboard](screenshots/leaderboard.png)

## Installation

1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Apply migrations: `python manage.py migrate`
5. Initialize game data: `python manage.py init_game_data`
6. Run the development server: `python manage.py runserver`

For detailed installation and deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Usage

1. Register an account or log in
2. Select a level to play
3. Match three identical blocks by clicking on them
4. Complete the level to unlock the next challenge
5. Check the leaderboard to see your ranking

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request


## Credits

- Game design and implementation by Tinting Yang
- Design specification by Xingyu Qian, Jiaxin Cheng, and Tingting Yang
- Icons by [Font Awesome](https://fontawesome.com/)
- CSS framework by [Bootstrap](https://getbootstrap.com/)
