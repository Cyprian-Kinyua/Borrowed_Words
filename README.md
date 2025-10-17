# 📖 BorrowedWords

**A peer-to-peer book lending platform connecting book lovers and builders of community libraries.**

Transform your dusty bookshelf into a revenue stream and give readers access to affordable books without breaking the bank. BorrowedWords makes it simple for book owners to share their collections and for readers to discover new stories nearby.

---

## 🎯 Quick Start

### Prerequisites

- Python 3.8+
- pip & virtualenv
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd borrowedwords

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Create .env file with:
# SECRET_KEY=your-secret-key
# DEBUG=True
# ALLOWED_HOSTS=localhost,127.0.0.1

# Run migrations & start server
python manage.py migrate
python manage.py runserver
```

The API will be live at `http://localhost:8000/api/`

---

## ✨ Features

### 🔐 Authentication & Profiles

- Secure JWT-based user authentication
- Customizable user profiles with bios and locations
- Distinct lender and borrower flows

### 📚 Book Management (Lenders)

- Add books with comprehensive metadata (title, author, ISBN, genre)
- Upload and manage book cover images
- Set daily rental prices
- Edit or deactivate listings anytime
- Track book availability in real-time

### 🔍 Book Discovery (Borrowers)

- Browse and search books by title, author, and genre
- Filter by availability and condition
- View detailed listings with owner information
- One-click borrow requests

### 🤝 Borrowing Workflow

- Instant notifications when requests arrive
- Lenders accept/reject with customizable due dates
- Real-time status tracking (pending → accepted → borrowed → returned → completed)
- Automated book availability updates
- Seamless return confirmation process

### 🚀 Coming Soon

- 💳 Secure payment integration
- 📍 Location-based discovery
- ⭐ Reviews & ratings system
- 📧 Automated due date reminders
- ⏳ Waitlist functionality

---

## 🏗️ Tech Stack

| Layer              | Technology                          |
| ------------------ | ----------------------------------- |
| **Backend**        | Django 4.x + Django REST Framework  |
| **Authentication** | JWT (djangorestframework-simplejwt) |
| **Database**       | SQLite (dev) / PostgreSQL (prod)    |
| **Image Storage**  | Django ImageField                   |
| **Frontend**       | React/Vue.js + Bootstrap/Bulma      |
| **Deployment**     | Heroku / PythonAnywhere             |

---

## 📡 API Endpoints

### Authentication

```
POST   /api/auth/register/        Register new user
POST   /api/auth/login/           Login (returns JWT token)
POST   /api/auth/logout/          Logout session
GET    /api/auth/user/            Get current user profile
```

### Books

```
GET    /api/books/                List all available books (searchable)
POST   /api/books/                Add new book (lenders only)
GET    /api/books/{id}/           Get book details
PUT    /api/books/{id}/           Update book (owner only)
DELETE /api/books/{id}/           Delete book (owner only)
GET    /api/me/books/             Get your listed books
```

### Transactions

```
GET    /api/transactions/             Get your transactions
POST   /api/transactions/             Create borrow request
POST   /api/transactions/{id}/accept/         Lender accepts request
POST   /api/transactions/{id}/reject/         Lender rejects request
POST   /api/transactions/{id}/mark-returned/  Borrower marks returned
POST   /api/transactions/{id}/confirm-return/ Lender confirms return
```

---

## 📦 Project Structure

```
borrowedwords/
├── users/              # Authentication & profiles
├── books/              # Book management
├── transactions/       # Borrow workflows
├── config/             # Django settings
└── requirements.txt
```

---

## 🗂️ Core Models

**User** — Extends Django's auth with location, phone, and bio  
**Book** — Represents a lendable book with owner, pricing, condition, and availability  
**BorrowTransaction** — Tracks complete loan lifecycle with status, dates, and fees

---

## 💡 How It Works

### For Lenders 🎁

1. Register & set up your profile
2. List your books with details and pricing
3. Review incoming requests
4. Accept & set return dates
5. Confirm returns to complete transactions

### For Borrowers 📖

1. Register & find books
2. Search or browse nearby collections
3. Send a borrow request
4. Track your active borrowings
5. Mark books as returned
6. Complete when lender confirms

---

## 🚀 Development Timeline

| Week | Focus       | Deliverables                                   |
| ---- | ----------- | ---------------------------------------------- |
| 1    | Foundation  | Django setup, JWT auth, endpoints ready        |
| 2    | Books       | CRUD operations, image uploads, filtering      |
| 3    | Workflow P1 | Borrow requests, transaction model, validation |
| 4    | Workflow P2 | Accept/reject/return logic, permissions        |
| 5    | Polish      | Frontend integration, testing, deployment      |

---

## 🤝 Contributing

We love contributions! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please follow our code style and include tests with your contributions.

---

## 📞 Support

Have questions? Open an issue or reach out to the [team](kingscyprian89@gmail.com). Happy lending! 📚✨
