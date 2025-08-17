# Maintainer Setup Guide

This guide is for setting up the IngressKit repository for OSS release.

## 🚀 **Pre-Launch Checklist**

### 1. Repository Setup
- [ ] **Replace main.py**: `mv server/main_oss.py server/main.py`
- [ ] **Replace requirements.txt**: `mv server/requirements_oss.txt server/requirements.txt`
- [ ] **Remove SaaS files**: Delete old `main.py` and billing-related code
- [ ] **Test locally**: Run `uvicorn server.main:app --host 0.0.0.0 --port 8080`

### 2. GitHub Configuration
- [ ] **Secrets**: Add `DOCKER_USERNAME` and `DOCKER_PASSWORD` to GitHub secrets
- [ ] **Discussions**: Enable GitHub Discussions with these categories:
  - General (default)
  - Q&A (default) 
  - Ideas (default)
  - Data Challenge (custom category for community challenges)
  - Schema Requests (custom category for new schemas)
  - Show and tell (default) - for community showcases
- [ ] **Issues**: Create issue templates for bugs, features, and schema requests
- [ ] **Branch protection**: Protect main branch, require PR reviews
- [ ] **GitHub Sponsors**: Set up GitHub Sponsors profile with tiered sponsorship
- [ ] **Sponsor button**: Verify `.github/FUNDING.yml` shows sponsor button in repo

### 3. Docker Hub Setup
- [ ] **Create repository**: `pilothobs/ingresskit` on Docker Hub
- [ ] **Automated builds**: Link to GitHub repository
- [ ] **Description**: Use README tagline and description

### 4. First Release
```bash
# Tag and push first release
git tag v0.1.0
git push origin v0.1.0

# This will trigger GitHub Actions to:
# - Run all tests
# - Build Docker images  
# - Push to Docker Hub
# - Create GitHub release
```

## 🔧 **Local Development**

### Build and Test Docker Images
```bash
# Build both variants
./scripts/build.sh

# Test server
docker run -p 8080:8080 pilothobs/ingresskit:latest &
curl http://localhost:8080/ping

# Test CLI
docker run -v $(pwd)/examples:/data pilothobs/ingresskit:core-local \
  --in /data/contacts_messy.csv --out /data/test_output.csv --schema contacts
```

### Test GitHub Actions Locally
```bash
# Install act (GitHub Actions runner)
# https://github.com/nektos/act

# Test the workflow
act push -j test-sdk
act push -j test-server
act push -j lint
```

## 📦 **Release Process**

### Version Bumping
1. Update version in relevant files:
   - `server/main_oss.py` (FastAPI app version)
   - `sdk/python/pyproject.toml` (package version)
   - `CHANGELOG.md` (new version section)

2. Create and push tag:
```bash
git tag v0.2.0
git push origin v0.2.0
```

3. GitHub Actions will automatically:
   - Build and test
   - Create Docker images with version tags
   - Create GitHub release with changelog

### Docker Image Tags
The CI creates these tags automatically:
- `pilothobs/ingresskit:latest` (main branch)
- `pilothobs/ingresskit:v0.1.0` (version tags)
- `pilothobs/ingresskit:core-latest` (CLI only)
- `pilothobs/ingresskit:core-v0.1.0` (CLI version)

## 🌟 **Launch Strategy**

### Phase 1: Soft Launch (Week 1)
- [ ] Push v0.1.0 to GitHub
- [ ] Verify Docker images work
- [ ] Test all documentation links
- [ ] Share with close network for feedback

### Phase 2: Community Launch (Week 2)
- [ ] **Show HN Post**: "IngressKit - Self-hosted data repair toolkit"
- [ ] **Reddit Posts**:
  - r/dataengineering: "Open-sourced our internal data ingestion toolkit"
  - r/selfhosted: "Self-hosted alternative to CSV processing SaaS"
  - r/opensource: "IngressKit - Privacy-first data normalization"

### Phase 3: Ecosystem Integration (Week 3+)
- [ ] Submit to Awesome lists:
  - [Awesome Data Engineering](https://github.com/igorbarinov/awesome-data-engineering)
  - [Awesome Self-Hosted](https://github.com/awesome-selfhosted/awesome-selfhosted)
  - [Awesome Python](https://github.com/vinta/awesome-python)
- [ ] **Product Hunt**: Submit as "Developer Tool of the Day"
- [ ] **Twitter/LinkedIn**: Share with developer communities

## 📊 **Success Metrics**

Track these metrics for OSS success:
- **GitHub Stars**: Target 100+ in first month
- **Docker Pulls**: Target 1,000+ in first month  
- **Contributors**: Target 5+ schema contributions
- **Issues/PRs**: Active community engagement
- **Show HN/Reddit**: Positive reception and discussion

### How to Enable GitHub Discussions
1. Go to repository Settings → General → Features
2. Check "Discussions" 
3. Set up categories:
   - Keep default: General, Q&A, Ideas, Show and tell
   - Add custom: "Data Challenge" and "Schema Requests"
4. Update landing page link from Issues back to Discussions

## 🤝 **Community Management**

### Responding to Issues
- **Bug Reports**: Acknowledge within 24h, fix within 1 week
- **Feature Requests**: Evaluate and label appropriately
- **Schema Requests**: Guide users through CONTRIBUTING.md

### Encouraging Contributions
- **Quick Wins**: Label easy issues as "good first issue"
- **Recognition**: Thank contributors in release notes
- **Documentation**: Keep CONTRIBUTING.md updated

### Data Challenge Management
- **Weekly Review**: Check new challenge submissions
- **Community Voting**: Let community vote on most interesting challenges
- **Solutions**: Document how IngressKit handles each challenge

## 🔒 **Security Considerations**

### Vulnerability Reporting
- Create SECURITY.md with reporting instructions
- Set up GitHub security advisories
- Monitor dependencies with Dependabot

### Code Review
- Require reviews for all PRs
- Run security scans in CI
- Validate all user inputs in server

## 📈 **Growth Strategy**

### Content Marketing
- **Blog Posts**: "Why we open-sourced our data ingestion toolkit"
- **Case Studies**: Real user implementations
- **Tutorials**: Integration with popular frameworks

### Developer Outreach
- **Conference Talks**: Data engineering meetups
- **Podcasts**: Developer-focused shows
- **Workshops**: Hands-on data processing sessions

### Partnership Opportunities
- **Integration Guides**: Popular data tools (Pandas, dbt, Airflow)
- **Cloud Marketplaces**: AWS/GCP/Azure marketplace listings
- **Developer Tools**: Integration with popular IDEs

---

**Ready to launch? Follow the checklist above and let's make IngressKit the go-to OSS data ingestion toolkit!** 🚀
