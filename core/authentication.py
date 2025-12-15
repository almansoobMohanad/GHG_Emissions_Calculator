"""Authentication utilities for the GHG Calculator app.

This module centralizes authentication concerns such as session state
initialization, credential validation, user registration, and logout.
It is intentionally framework-light (only uses Streamlit for session state)
so it can be re-used across pages.
"""

import hashlib
import streamlit as st
from core.cache import get_database


def init_session_state():
	"""Initialize auth-related keys in Streamlit session state.

	Ensures the app always has the expected keys available without
	overwriting any existing values set earlier in the session.
	"""
	defaults = {
		'authenticated': False,
		'user_id': None,
		'username': None,
		'email': None,
		'role': None,
		'company_id': None,
		'show_register': False,
	}
	for key, value in defaults.items():
		if key not in st.session_state:
			st.session_state[key] = value


def hash_password(password: str) -> str:
	"""Return a SHA-256 hash of the given password string.

	Args:
		password: Plaintext password to hash.

	Returns:
		Hexadecimal string of the SHA-256 digest.

	Note:
		For production environments, prefer an adaptive hashing algorithm
		like bcrypt or argon2 with per-user salts.
	"""
	return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username: str, password: str):
	"""Validate credentials against the database.

	Args:
		username: Account username.
		password: Plaintext password to validate.

	Returns:
		Tuple[user_dict|None, str|None]:
			- user_dict on success with keys:
			  `id`, `username`, `email`, `role`, `company_id`,
			  `company_name`, `company_verified`.
			- error message string on failure (None on success).
	"""
	db = get_database()
	if not db.connect():
		return None, "Database connection failed"

	try:
		password_hash = hash_password(password)
		query = (
			"""
			SELECT u.id, u.username, u.email, u.role, u.company_id, u.is_active,
				   c.company_name, c.verification_status
			FROM users u
			LEFT JOIN companies c ON u.company_id = c.id
			WHERE u.username = %s AND u.password_hash = %s
			"""
		)
		row = db.fetch_one(query, (username, password_hash))

		if not row:
			return None, "Invalid username or password"

		if not row[5]:  # is_active
			return None, "Account is inactive"

		user = {
			'id': row[0],
			'username': row[1],
			'email': row[2],
			'role': row[3],
			'company_id': row[4],
			'company_name': row[6],
			'company_verified': (row[7] == 'verified'),
		}
		return user, None
	finally:
		db.disconnect()


def register_user(username: str, email: str, password: str):
	"""Create a new user account.

	Args:
		username: Desired username (must be unique).
		email: Email address (must be unique).
		password: Plaintext password to hash and store.

	Returns:
		Tuple[bool, str]: (success flag, human-friendly message).
	"""
	db = get_database()
	if not db.connect():
		return False, "Database connection failed"

	try:
		# Ensure unique username/email
		existing = db.fetch_one(
			"SELECT id FROM users WHERE username = %s OR email = %s",
			(username, email),
		)
		if existing:
			return False, "Username or email already exists"

		password_hash = hash_password(password)
		insert_query = (
			"""
			INSERT INTO users (username, email, password_hash, role, is_active)
			VALUES (%s, %s, %s, 'normal_user', TRUE)
			"""
		)
		new_id = db.execute_query(insert_query, (username, email, password_hash), return_id=True)
		if new_id:
			return True, "Registration successful! Please login."
		return False, "Registration failed"
	finally:
		db.disconnect()


def set_authenticated_session(user: dict):
	"""Populate session state after a successful login.

	Args:
		user: Mapping with keys `id`, `username`, `email`, `role`, `company_id`.
	"""
	st.session_state.authenticated = True
	st.session_state.user_id = user['id']
	st.session_state.username = user['username']
	st.session_state.email = user['email']
	st.session_state.role = user['role']
	st.session_state.company_id = user['company_id']


def logout(clear_all: bool = True):
	"""Clear session state and rerun the app to reflect logout.

	Args:
		clear_all: When True, remove all keys from session state.
				  When False, only reset authentication-related keys.
	"""
	if clear_all:
		for key in list(st.session_state.keys()):
			del st.session_state[key]
	else:
		st.session_state.authenticated = False
		st.session_state.user_id = None
		st.session_state.username = None
		st.session_state.email = None
		st.session_state.role = None
		st.session_state.company_id = None
	st.rerun()
