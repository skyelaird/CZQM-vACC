# CZQM MAESTRO Project

Multi-user Arrival Manager (AMAN) system for CZQM/CZQX vACC controllers.

## Overview

This project implements a centralized MAESTRO arrival management system that allows multiple controllers to coordinate arrival sequencing in real-time.  Based on the TopSky MAESTRO plugin by Juha Holopainen, extended with server-based Master/Slave synchronization.

## Project Status

🚧 **In Development** - Not yet deployed to production

## Features

- **Master/Slave Architecture**: One controller manages sequence, others view in real-time
- **Multi-Airport Support**: CYHZ (Halifax), CYYT (St. John's), CYQX (Gander)
- **Automatic Sequencing**: Calculates delays and spacing automatically
- **Real-time Synchronization**: All controllers see the same sequence data
- **Server-Based**: Centralized Node.js server for data persistence

## Project Structure

```
MAESTRO/
├── server/                  # Node.js synchronization server
│   ├── czqm-maestro-server.js
│   └── package.json
├── sync-tool/               # External sync tool (future)
│   └── README.md
├── config/                  # Configuration files
│   └── airports.json
├── docs/                    # Documentation
│   ├── DEPLOYMENT.md
│   ├── CZQM-MAESTRO-Training-Guide.md
│   ├── MAESTRO-Quick-Reference.md
│   └── MAESTRO-Integration-Guide.md
└── README.md (this file)
```

## Quick Start

### For Controllers

1. **Load MAESTRO Plugin** in EuroScope
2. **Connect to Server**:
   - MASTER: "Connect as MASTER (Web+Local)"
   - SLAVE: "Connect as SLAVE (Web+Local)"
3. See Training Guide for detailed instructions

### For Server Administrators

1. **Install Dependencies**:
   ```bash
   cd server
   npm install
   ```

2. **Start Server**:
   ```bash
   npm start
   ```

3. See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production setup

## Documentation

- **[Training Guide](docs/CZQM-MAESTRO-Training-Guide.md)** - Comprehensive controller training manual
- **[Quick Reference](docs/MAESTRO-Quick-Reference.md)** - One-page reference card
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Server installation and configuration
- **[Integration Guide](docs/MAESTRO-Integration-Guide.md)** - Technical integration details

## Requirements

### Controllers
- EuroScope 3.2+
- TopSky plugin with MAESTRO
- Network access to MAESTRO server

### Server
- Node.js 16+
- 256MB RAM minimum
- Persistent internet connection
- Open port 3000 (or configured port)

## Implementation Roadmap

### Phase 1: Server Development ✅
- [x] Node.js REST API
- [x] Master/Slave coordination
- [x] Airport configuration
- [x] Basic documentation

### Phase 2: Integration (Current)
- [ ] Deploy test server
- [ ] Develop sync tool
- [ ] Test with 2-3 controllers
- [ ] Refine coordination procedures

### Phase 3: Training
- [ ] Create video tutorials
- [ ] Conduct sweatbox training
- [ ] Test during low-traffic periods
- [ ] Document best practices

### Phase 4: Production
- [ ] Deploy production server
- [ ] Full controller rollout
- [ ] Use for CTP events
- [ ] Continuous improvement

## Support

- **Issues**: [GitHub Issues](https://github.com/skyelaird/CZQM-vACC/issues)
- **Discord**: #czqm-maestro-support
- **Email**: ops@czqm.ca

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

GPL-3.0 - See [LICENSE](../LICENSE) for details

## Credits

- **TopSky/MAESTRO Plugin**: Juha Holopainen
- **Server Development**: CZQM vACC Technical Team
- **Documentation**: CZQM Operations & Training
- **Testing**: CZQM Controllers

## Related Projects

- [CZQM TopSky](../TopSky/) - TopSky radar configuration
- [CZQM Sector Files](../sectors/) - EuroScope sector files
- [VATSIM UK Controller Pack](https://github.com/VATSIM-UK/uk-controller-pack) - Inspiration

## Changelog

### v1.0.0 (In Development)
- Initial server implementation
- Multi-airport support (CYHZ, CYYT, CYQX)
- Comprehensive documentation
- Training materials

---

**Last Updated**: November 30, 2025  
**Maintainer**: Joel Laird (VE1ATM / skyelaird)
