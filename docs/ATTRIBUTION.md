# Attribution and Licensing

## Project Foundation

This project is based on the **OpenAI Agents Python SDK Financial Research Agent Example**.

**Source:** https://github.com/openai/openai-agents-python/tree/main/examples/financial_research_agent

**License:** MIT License (Copyright OpenAI)

**Modifications:**
- Enhanced multi-agent architecture with specialized financial and risk agents
- Integrated SEC EDGAR data extraction via edgartools library
- Added comprehensive financial statement extraction (118+ line items)
- Implemented cost-optimization with GPT-5 model selection
- Added comparative period financial analysis

---

## SEC EDGAR Data Extraction

### edgartools Library

This project uses the **edgartools** Python library for comprehensive SEC EDGAR data extraction.

**Author:** Dwight Gunning
**Repository:** https://github.com/dgunning/edgartools
**License:** MIT License
**PyPI:** https://pypi.org/project/edgartools/

**Usage:**
- Direct extraction of financial statements from SEC EDGAR filings
- Access to complete XBRL data (118+ line items per company)
- Balance sheet, income statement, and cash flow statement extraction
- Comparative period analysis (current vs. prior period)

**Citation:**
```
Gunning, D. (2024). edgartools: Python library for accessing SEC EDGAR filings.
https://github.com/dgunning/edgartools
```

---

## SEC EDGAR MCP Server

This project uses the **SEC EDGAR MCP (Model Context Protocol) Server** for accessing official SEC filing data.

### Citation

**APA Style:**
```
Amorelli, S. (2025). SEC EDGAR MCP (Model Context Protocol) Server (Version 1.0.6)
[Computer software]. Zenodo. https://doi.org/10.5281/zenodo.17123166
```

**BibTeX:**
```bibtex
@software{amorelli_sec_edgar_mcp_2025,
  title = {{SEC EDGAR MCP (Model Context Protocol) Server}},
  author = {Amorelli, Stefano},
  version = {1.0.6},
  year = {2025},
  month = {9},
  url = {https://doi.org/10.5281/zenodo.17123166},
  doi = {10.5281/zenodo.17123166}
}
```

### License

The SEC EDGAR MCP Server is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

**Key Terms:**
- You may use, modify, and distribute this software
- Any modifications must also be released under AGPL-3.0
- If you run a modified version on a server, you must provide the source code to users
- Network use (API/service) triggers the license (unlike regular GPL)

**Source:** https://github.com/stefanoamorelli/sec-edgar-mcp

**License Text:** https://github.com/stefanoamorelli/sec-edgar-mcp/blob/main/LICENSE

### AGPL-3.0 Compliance

#### Our Usage
This project uses the SEC EDGAR MCP Server as a **dependency** via:
- `uvx sec-edgar-mcp` (recommended)
- Docker: `stefanoamorelli/sec-edgar-mcp:latest`
- PyPI: `pip install sec-edgar-mcp`

We have **not modified** the SEC EDGAR MCP Server source code. We use it as-is via the Model Context Protocol (MCP) interface.

#### Your Obligations

**If you are using this code as-is (no modifications):**
- ✅ You're using the SEC EDGAR MCP Server via its standard interface
- ✅ No additional obligations beyond attribution
- ✅ Include this ATTRIBUTION.md file if distributing

**If you modify this financial research agent code:**
- ⚠️ Your modifications to THIS codebase are your own
- ⚠️ The SEC EDGAR MCP Server remains under AGPL-3.0
- ⚠️ You don't need to release your agent code under AGPL (it's separate)

**If you modify the SEC EDGAR MCP Server itself:**
- ❗ You MUST release your modifications under AGPL-3.0
- ❗ You MUST provide source code to users if running as a service
- ❗ Contact stefano@amorelli.tech for commercial licensing alternatives

#### Network Use Trigger

The AGPL-3.0 has a "network use" provision:
- If you modify the SEC EDGAR MCP Server and offer it as a service (API, web app), you must provide the source code to users
- Simply using our financial research agent (even as a service) does NOT trigger this - only modifications to the MCP server itself

### Summary

**For Academic/Research Use:**
- Include the APA or BibTeX citation in your papers
- Acknowledge the SEC EDGAR MCP Server in your methods section

**For Commercial Use:**
- Using the unmodified SEC EDGAR MCP Server is permitted under AGPL-3.0
- Include this attribution file
- For commercial licensing without AGPL obligations, contact: stefano@amorelli.tech

**For Open Source Projects:**
- Include this ATTRIBUTION.md file
- Reference the SEC EDGAR MCP Server in your README
- Link to: https://github.com/stefanoamorelli/sec-edgar-mcp

---

## Other Dependencies

### OpenAI Agents SDK
- **License:** Apache 2.0
- **Source:** https://github.com/openai/openai-agents
- **Usage:** Agent orchestration framework

### Rich
- **License:** MIT
- **Source:** https://github.com/Textualize/rich
- **Usage:** Terminal UI/output formatting

### Python-dotenv
- **License:** BSD-3-Clause
- **Source:** https://github.com/theskumar/python-dotenv
- **Usage:** Environment variable management

---

## SEC Data Source

All financial data accessed via the SEC EDGAR MCP Server comes from the **U.S. Securities and Exchange Commission (SEC)**.

**Data Source:** https://www.sec.gov/edgar

**Terms of Use:** https://www.sec.gov/privacy

**Attribution:**
```
Financial data sourced from the U.S. Securities and Exchange Commission
via SEC EDGAR database. https://www.sec.gov/edgar
```

**User-Agent Requirement:**
The SEC requires all automated access to identify the requestor via User-Agent header:
```
SEC_EDGAR_USER_AGENT=YourCompany/Version (contact@email.com)
```
See: https://www.sec.gov/os/accessing-edgar-data

---

## Questions?

**SEC EDGAR MCP Server licensing:** stefano@amorelli.tech

**This project:** See repository maintainer

**SEC data access:** https://www.sec.gov/developer
