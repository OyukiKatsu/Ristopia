# Ristòpia 🍽️

**Ristòpia** is a web application that allows restaurant owners to register and manage their establishments through an interactive map-based interface. Customers can use the platform to order food by scanning a unique QR code per table, streamlining the dining experience.

---

## 📌 Project Overview

- **Project Title:** Ristòpia
- **Project Description:**  
  A web application designed to let restaurant owners manage their dining spaces graphically. It enables customers to order through QR codes and facilitates communication between staff roles like waiters and cooks.
- **Problem Statement:**  
  There is a lack of a web solution that allows restaurant owners to easily and visually manage their spaces and streamline internal operations.
- **Technological Stack:**
  - Backend: Django
  - Frontend: JavaScript, Vue.js, HTML, CSS (Tailwind CSS)
  - Database: MySQL

---

## 📐 Project Description

The application is divided into three main modules: **Client**, **Restaurant**, and **Staff**.

### 🍴 Restaurant Module

- Owners can visually create a floor plan of their restaurant.
- Define areas like tables and counters for ready dishes.
- Generate unique QR codes per table.
- Register staff (waiters, cooks) and assign them auto-generated alphanumeric login codes.

### 👩‍🍳 Staff Module

- Workers log in using the unique code provided by the owner.
- Roles define UI and permissions (Waiter/Cook).
- Waiters see customer orders and confirm them.(Not definitive method)
- Cooks see confirmed orders, mark items as ready, and track status.

### 📱 Client Module

- Clients scan a QR code upon sitting.
- They can browse the menu, add items to an order list, and mark as ready.
- The request flows to the waiter interface for confirmation(Not definitive method), then to the cook’s dashboard.

### 💵 Order & Menu Management

- View current orders per table with total cost.
- Release tables after completion.
- Add, enable, or disable menu items dynamically.

---

## 🚧 To-Do List

### ✅ Backend API

- [x] POST-API for `Profile`
- [x] POST-API for `Restaurant`
- [x] POST-API for `Menu`
- [x] POST-API for `Category`
- [x] POST-API for `CategoryElement`

### 🛠️ Still to do

- [ ] GET/PUT/DELETE APIs for all models
- [ ] QR Code generation for tables
- [ ] Graphical floor plan editor
- [ ] Staff login system via unique code
- [ ] Role-based UI rendering (Waiter/Cook)
- [ ] Client menu interface via QR code
- [ ] Real-time order updates between staff
- [ ] Table release and total calculation
- [ ] Menu item management (activation/deactivation)

---

## 🗒️ Development Notes
- All API calls have crsf disable for testing with Postman 

