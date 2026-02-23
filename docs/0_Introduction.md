# Sustainability Monitoring Hub - Documentation

## Introduction

Welcome to the **Sustainability Monitoring Hub**, a comprehensive Streamlit-based platform for managing company-level sustainability operations. This documentation guide provides all technical and user information needed to deploy, configure, and operate the system effectively.

## About This Project

The Sustainability Monitoring Hub combines GHG emissions tracking with verification workflows, ESG reporting/disclosure modules, document exchange, and reduction roadmap planning. The platform is designed to streamline sustainability data management and support organizations in their journey toward net-zero commitments.

**Key Features:**
- Real-time GHG emissions tracking and calculation
- Multi-level verification and audit trail workflows
- SEDG and ESG readiness reporting
- Emission factor management with custom source support
- Reduction goal tracking and initiative management
- Inter-company document request system
- COSIRI document repository

## Project Information

**Project Name:** Sustainability Monitoring Hub

**Version:** 1.0.0

**Status:** Active Development

**Last Updated:** February 2026

## Scope of This Documentation

This 7-part documentation set covers:

1. **System Architecture** - High-level system design, component overview, and data flow
2. **Database Schema** - Complete database structure and relationship documentation
3. **Technical Documentation** - Core modules, caching, authentication, and integration details
4. **API Documentation** - Function signatures and usage for core modules and utilities
5. **User Guides** - End-user documentation for all app features and workflows
6. **Deployment Guide** - Installation, configuration, and production deployment steps
7. **GHG Protocol Schema** - Scope and category definitions aligned with GHG Protocol standards

## Quick Start

For **first-time users and deployers:**
1. Read the Deployment Guide (Section 6) for setup instructions
2. Review the User Guides (Section 5) to understand available features
3. Consult the System Architecture (Section 1) for understanding the overall design

For **developers and system administrators:**
1. Start with System Architecture (Section 1) for an overview
2. Review Database Schema (Section 2) to understand data structure
3. Consult Technical Documentation (Section 3) for module implementation details
4. Reference API Documentation (Section 4) for function signatures

## Technology Stack

- **Frontend/Application Framework:** Streamlit
- **Data Analysis & Visualization:** pandas, Plotly
- **Database:** MySQL 8.x
- **PDF Generation:** reportlab, fpdf2
- **Geocoding:** geopy
- **Environment Management:** python-dotenv

## System Requirements

- Python 3.10 or higher
- MySQL 8.x server
- 2+ GB available RAM
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Getting Help

- Review relevant sections in this documentation
- Check troubleshooting guides in the Deployment Guide
- Consult inline code comments in the repository
- Review error logs in the application output

## Document Navigation

Each section of this documentation can be read independently, though cross-references are provided where relevant. Headers and sub-sections are clearly marked for easy navigation.

---

**For Questions or Issues:** Contact the development team or refer to the Troubleshooting sections in the Deployment Guide.

**License:** Open Source - MIT License

**Author:** Mohanad Al-Mansoob

**Document Generated:** February 23, 2026
