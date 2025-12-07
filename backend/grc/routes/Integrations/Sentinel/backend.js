const express = require('express');
const session = require('express-session');
const path = require('path');
const axios = require('axios');
const crypto = require('crypto');
const zlib = require('zlib');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// ==================== SERVICE CLASSES ====================

// OAuth Service
class SentinelOAuthService {
  constructor() {
    this.clientId = process.env.MICROSOFT_CLIENT_ID || '1d9fdf2e-ebc8-47e0-8e7d-4c4c41b6a616';
    this.clientSecret = process.env.MICROSOFT_CLIENT_SECRET;
    this.tenantId = process.env.MICROSOFT_TENANT_ID || 'aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6';
    this.redirectUri = process.env.REDIRECT_URI || 'http://localhost:3000/auth/sentinel/callback';
    this.scope = 'https://graph.microsoft.com/.default';
  }

  getAuthorizationUrl(state) {
    const authUrl = new URL(`https://login.microsoftonline.com/${this.tenantId}/oauth2/v2.0/authorize`);
    authUrl.searchParams.set('client_id', this.clientId);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('redirect_uri', this.redirectUri);
    authUrl.searchParams.set('scope', this.scope);
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('response_mode', 'query');
    authUrl.searchParams.set('prompt', 'login');
    return authUrl.toString();
  }

  async exchangeCodeForToken(authCode) {
    const tokenUrl = `https://login.microsoftonline.com/${this.tenantId}/oauth2/v2.0/token`;
    const params = new URLSearchParams();
    params.append('client_id', this.clientId);
    params.append('client_secret', this.clientSecret);
    params.append('code', authCode);
    params.append('grant_type', 'authorization_code');
    params.append('redirect_uri', this.redirectUri);
    params.append('scope', this.scope);

    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Token exchange failed: ${errorData.error_description || errorData.error}`);
    }

    return await response.json();
  }

  async refreshAccessToken(refreshToken) {
    const tokenUrl = `https://login.microsoftonline.com/${this.tenantId}/oauth2/v2.0/token`;
    const params = new URLSearchParams();
    params.append('client_id', this.clientId);
    params.append('client_secret', this.clientSecret);
    params.append('refresh_token', refreshToken);
    params.append('grant_type', 'refresh_token');
    params.append('scope', this.scope);

    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Token refresh failed: ${errorData.error_description || errorData.error}`);
    }

    return await response.json();
  }

  generateRandomState() {
    return crypto.randomBytes(32).toString('hex');
  }

  verifyState(state, sessionState) {
    return state === sessionState;
  }
}

// Sentinel Auth Service
class SentinelAuthService {
  constructor() {
    this.clientId = process.env.MICROSOFT_CLIENT_ID || '1d9fdf2e-ebc8-47e0-8e7d-4c4c41b6a616';
    this.clientSecret = process.env.MICROSOFT_CLIENT_SECRET;
    this.tenantId = process.env.MICROSOFT_TENANT_ID || 'aa7c8c45-41a3-4453-bc9a-3adfe8ff5fb6';
    this.scope = 'https://graph.microsoft.com/.default';
  }

  async authenticateWithCredentials(email, password) {
    try {
      console.log('🔐 Authenticating with Microsoft using Resource Owner Password Credential flow');
      const tokenUrl = `https://login.microsoftonline.com/${this.tenantId}/oauth2/v2.0/token`;
      
      const params = new URLSearchParams();
      params.append('client_id', this.clientId);
      params.append('client_secret', this.clientSecret);
      params.append('scope', this.scope);
      params.append('username', email);
      params.append('password', password);
      params.append('grant_type', 'password');

      const response = await axios.post(tokenUrl, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const tokenData = response.data;
      const userInfo = await this.getUserInfo(tokenData.access_token);

      return {
        success: true,
        accessToken: tokenData.access_token,
        refreshToken: tokenData.refresh_token,
        expiresIn: tokenData.expires_in,
        tokenExpiry: Date.now() + (tokenData.expires_in * 1000),
        userInfo: userInfo
      };
    } catch (error) {
      console.error('❌ Authentication failed:', error.response?.data || error.message);
      let errorMessage = 'Authentication failed';
      if (error.response?.data?.error_description) {
        errorMessage = error.response.data.error_description;
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      }
      return { success: false, error: errorMessage };
    }
  }

  async getUserInfo(accessToken) {
    try {
      const response = await axios.get('https://graph.microsoft.com/v1.0/me', {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      return {
        id: response.data.id,
        displayName: response.data.displayName,
        userPrincipalName: response.data.userPrincipalName,
        mail: response.data.mail
      };
    } catch (error) {
      return {
        id: 'unknown',
        displayName: 'User',
        userPrincipalName: 'user@domain.com',
        mail: 'user@domain.com'
      };
    }
  }

  async testDefenderConnection(accessToken) {
    try {
      const testUrl = 'https://graph.microsoft.com/v1.0/security/incidents?$top=1';
      const response = await axios.get(testUrl, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });
      return { success: true, incidentCount: response.data.value?.length || 0 };
    } catch (error) {
      return { success: false, error: error.response?.data?.error?.message || error.message };
    }
  }

  async refreshToken(refreshToken) {
    try {
      const tokenUrl = `https://login.microsoftonline.com/${this.tenantId}/oauth2/v2.0/token`;
      const params = new URLSearchParams();
      params.append('client_id', this.clientId);
      params.append('client_secret', this.clientSecret);
      params.append('refresh_token', refreshToken);
      params.append('grant_type', 'refresh_token');
      params.append('scope', this.scope);

      const response = await axios.post(tokenUrl, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      return {
        success: true,
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token || refreshToken,
        expiresIn: response.data.expires_in,
        tokenExpiry: Date.now() + (response.data.expires_in * 1000)
      };
    } catch (error) {
      return { success: false, error: error.response?.data?.error_description || error.message };
    }
  }
}

// Query Decompressor
class QueryDecompressor {
  static async decompressQuery(compressedQuery) {
    try {
      const base64Match = compressedQuery.match(/'([A-Za-z0-9+/=]+)'/);
      if (!base64Match) throw new Error('No base64 data found in query');
      
      const base64Data = base64Match[1];
      const buffer = Buffer.from(base64Data, 'base64');
      
      let decompressed;
      try {
        decompressed = zlib.inflateSync(buffer);
      } catch (e1) {
        try {
          decompressed = zlib.gunzipSync(buffer);
        } catch (e2) {
          decompressed = zlib.inflateRawSync(buffer);
        }
      }
      
      const decompressedString = decompressed.toString('utf-8');
      return this.parseKQLResult(decompressedString);
    } catch (error) {
      console.error('❌ Error decompressing query:', error.message);
      return null;
    }
  }
  
  static parseKQLResult(kqlResult) {
    try {
      let jsonData = null;
      try {
        jsonData = JSON.parse(kqlResult);
      } catch (e) {}
      
      const emailRegex = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
      const emails = kqlResult.match(emailRegex) || [];
      
      const userPatterns = [
        /(?:user|account|email|mailbox|upn|username)[:\s=]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/gi,
        /"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"/g,
        /\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b/g
      ];
      
      const allUserMatches = [];
      for (const pattern of userPatterns) {
        const matches = [...kqlResult.matchAll(pattern)];
        allUserMatches.push(...matches.map(m => m[1]));
      }
      
      const uniqueUsers = [...new Set(allUserMatches)];
      
      const actionPatterns = [
        /(?:action|operation|activity|command|ActionsPerformed)[:\s=]+"([^"]+)"/gi,
        /ActionsPerformed[:\s]*\["([^"]+)"\]/gi,
        /"([^"]*(?:add|remove|create|delete|modify|change|update)[^"]*)"/gi
      ];
      
      const allActionMatches = [];
      for (const pattern of actionPatterns) {
        const matches = [...kqlResult.matchAll(pattern)];
        allActionMatches.push(...matches.map(m => m[1]));
      }
      
      const genericActions = ['action', 'operation', 'activity', 'command', 'performed', 'detected', 'sensitive', 'operations'];
      const uniqueActions = [...new Set(allActionMatches)].filter(a => 
        a && !genericActions.includes(a.toLowerCase())
      );
      
      const result = {
        rawData: kqlResult,
        jsonData: jsonData,
        emails: emails || [],
        users: uniqueUsers || [],
        actions: uniqueActions || [],
        hasData: false
      };
      
      if (jsonData) {
        if (jsonData.User) {
          result.primaryUser = jsonData.User;
          result.hasData = true;
        }
        if (jsonData.ActionsPerformed && Array.isArray(jsonData.ActionsPerformed)) {
          result.primaryAction = jsonData.ActionsPerformed[0];
        }
        if (jsonData.AlertDescription) {
          result.alertDescription = jsonData.AlertDescription;
        }
      }
      
      if (!result.hasData && (result.emails.length > 0 || result.users.length > 0)) {
        result.hasData = true;
        result.primaryUser = result.users[0] || result.emails[0];
      }
      
      if (!result.primaryAction && result.actions.length > 0) {
        result.primaryAction = result.actions[0];
      }
      
      return result;
    } catch (error) {
      return { rawData: kqlResult, hasData: false };
    }
  }
  
  static async extractEnrichedUserData(alert) {
    try {
      if (!alert.additionalData || !alert.additionalData.Query) return null;
      
      const decompressed = await this.decompressQuery(alert.additionalData.Query);
      
      if (decompressed && decompressed.hasData) {
        return {
          user: decompressed.primaryUser,
          action: decompressed.primaryAction,
          alertDescription: decompressed.alertDescription,
          allEmails: decompressed.emails,
          allActions: decompressed.actions,
          source: 'decompressed_query'
        };
      }
      
      return null;
    } catch (error) {
      return null;
    }
  }
}

// Defender API Service
class DefenderAPIService {
  constructor(accessToken) {
    this.accessToken = accessToken;
    this.baseUrl = 'https://graph.microsoft.com/v1.0/security';
  }

  async getIncidents(filters = {}) {
    try {
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const sevenDaysAgoISO = sevenDaysAgo.toISOString();
      
      let url = `${this.baseUrl}/incidents?$top=50`;
      const oDataFilters = [`createdDateTime ge ${sevenDaysAgoISO}`];
      
      if (oDataFilters.length > 0) {
        url += `&$filter=${encodeURIComponent(oDataFilters.join(' and '))}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        let errorDetails = '';
        try {
          const errorData = await response.json();
          errorDetails = errorData.error?.message || JSON.stringify(errorData);
        } catch (e) {
          errorDetails = await response.text();
        }
        throw new Error(`Defender API Error: ${response.status} - ${errorDetails}`);
      }

      const data = await response.json();
      let allIncidents = data.value || [];
      
      let nextLink = data['@odata.nextLink'];
      let pageCount = 1;
      
      while (nextLink && pageCount < 3) {
        const nextResponse = await fetch(nextLink, {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (nextResponse.ok) {
          const nextData = await nextResponse.json();
          allIncidents = allIncidents.concat(nextData.value || []);
          nextLink = nextData['@odata.nextLink'];
          pageCount++;
        } else {
          break;
        }
      }
      
      let incidents = this.transformIncidents(allIncidents);
      const groupedIncidents = this.groupIncidentsByID(incidents);
      
      const dateThreshold = new Date();
      dateThreshold.setDate(dateThreshold.getDate() - 7);
      
      let filteredIncidents = groupedIncidents.filter(incident => {
        const createdDate = new Date(incident.createdTime);
        return createdDate >= dateThreshold;
      });
      
      if (!filters.includeAll && !filters.status) {
        filteredIncidents = filteredIncidents.filter(incident => 
          incident.status === 'New' || incident.status === 'Active'
        );
      } else if (filters.status && filters.status !== 'All') {
        filteredIncidents = filteredIncidents.filter(incident => 
          incident.status === filters.status
        );
      }
      
      if (filters.severity) {
        filteredIncidents = filteredIncidents.filter(incident => 
          incident.severity.toLowerCase() === filters.severity.toLowerCase()
        );
      }
      
      return filteredIncidents;
    } catch (error) {
      console.error('❌ Error fetching incidents:', error);
      throw error;
    }
  }

  async getIncident(incidentId) {
    const url = `${this.baseUrl}/incidents/${incidentId}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) throw new Error(`Failed to fetch incident: ${response.status}`);
    const incident = await response.json();
    return this.transformIncident(incident);
  }

  async getIncidentAlerts(incidentId) {
    try {
      const incidentUrl = `${this.baseUrl}/incidents/${incidentId}`;
      const incidentResponse = await fetch(incidentUrl, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!incidentResponse.ok) throw new Error(`Failed to fetch incident`);
      const incident = await incidentResponse.json();

      let alerts = [];
      const filterAttempts = [
        `incidentId eq '${incidentId}'`,
        `incidentId eq ${incidentId}`
      ];
      
      for (const filter of filterAttempts) {
        const listUrl = `https://graph.microsoft.com/v1.0/security/alerts_v2?$filter=${encodeURIComponent(filter)}&$top=100`;
        
        try {
          const listResponse = await fetch(listUrl, {
            headers: {
              'Authorization': `Bearer ${this.accessToken}`,
              'Content-Type': 'application/json'
            }
          });

          if (listResponse.ok) {
            const listData = await listResponse.json();
            alerts = listData.value || [];
            if (alerts.length > 0) break;
          }
        } catch (error) {}
      }

      if (alerts.length === 0) {
        const allAlertsUrl = `https://graph.microsoft.com/v1.0/security/alerts_v2?$top=200&$orderby=createdDateTime desc`;
        const allAlertsResponse = await fetch(allAlertsUrl, {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          }
        });

        if (allAlertsResponse.ok) {
          const allAlertsData = await allAlertsResponse.json();
          const allAlerts = allAlertsData.value || [];
          alerts = allAlerts.filter(alert => {
            return alert.incidentId === incidentId || 
                   alert.incidentId === String(incidentId) || 
                   alert.incidentId === parseInt(incidentId);
          });
        }
      }

      if (alerts.length > 0) {
        return await this.transformAlertsToDetailedFormat(alerts, incident);
      }

      return [];
    } catch (error) {
      console.error('❌ Error in getIncidentAlerts:', error);
      throw error;
    }
  }

  async transformAlertsToDetailedFormat(alerts, incident) {
    const transformedAlerts = [];
    
    for (let index = 0; index < alerts.length; index++) {
      const alert = alerts[index];
      
      const timeGenerated = alert.createdDateTime || 
                           alert.firstActivityDateTime || 
                           incident.createdDateTime ||
                           new Date().toISOString();
      
      let enrichedData = null;
      try {
        enrichedData = await QueryDecompressor.extractEnrichedUserData(alert);
      } catch (error) {}
      
      let user = enrichedData?.user || null;
      
      if (!user && alert.userStates && Array.isArray(alert.userStates) && alert.userStates.length > 0) {
        const userState = alert.userStates.find(us => us.userPrincipalName || us.accountName);
        if (userState) {
          user = userState.userPrincipalName || userState.accountName;
        }
      }
      
      if (!user && alert.entities && Array.isArray(alert.entities)) {
        const userEntity = alert.entities.find(e => {
          const odataType = e['@odata.type'] || '';
          return odataType.includes('user') || odataType.includes('mailbox');
        });
        if (userEntity) {
          user = userEntity.userPrincipalName || userEntity.mailboxPrimaryAddress || userEntity.accountName;
        }
      }
      
      if (!user && alert.evidence && Array.isArray(alert.evidence)) {
        const userEvidence = alert.evidence.find(e => {
          const odataType = e['@odata.type'] || '';
          return odataType.includes('user') || odataType.includes('mailbox');
        });
        if (userEvidence && userEvidence.userAccount) {
          user = userEvidence.userAccount.userPrincipalName || userEvidence.userAccount.accountName;
        }
      }
      
      if (!user) {
        const text = `${alert.title || ''} ${alert.description || ''}`;
        const emailMatch = text.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
        if (emailMatch) user = emailMatch[1];
      }
      
      let actionsPerformed = enrichedData?.action ? [enrichedData.action] : this.extractActionsFromAlert(alert, incident);
      
      if (actionsPerformed && actionsPerformed.length > 0) {
        const genericActions = ['Suspicious activity detected', 'SuspiciousActivity', 'Unknown'];
        if (genericActions.includes(actionsPerformed[0])) {
          actionsPerformed = null;
        }
      }
      
      const suspiciousActivityCount = this.extractSuspiciousActivityCount(alert);
      
      let alertDescription = enrichedData?.alertDescription || 
                              alert.description || 
                              alert.title || 
                              'No description available';
      
      const transformed = {
        id: alert.id || `alert-${index}`,
        timeGenerated: timeGenerated,
        actionsPerformed: actionsPerformed,
        alertDescription: alertDescription,
        suspiciousActivityCount: suspiciousActivityCount,
        user: user,
        severity: this.mapSeverity(alert.severity || incident.severity || 'Informational'),
        status: this.mapStatus(alert.status || incident.status || 'Active'),
        category: alert.category || 'Unknown',
        title: alert.title || incident.displayName || 'Untitled Alert',
        detectionSource: alert.detectionSource || 'Microsoft Defender',
        productName: alert.productName || 'Microsoft Defender',
        fullAlertData: alert
      };
      
      transformedAlerts.push(transformed);
    }
    
    return transformedAlerts;
  }

  extractActionsFromAlert(alert, incident) {
    const actions = [];
    const text = `${alert.title || ''} ${alert.description || ''}`.toLowerCase();
    
    const actionPatterns = [
      { pattern: /add(?:ed|ing)?\s+(?:member|user)\s+to\s+(?:group|role)/i, action: 'Add member to group' },
      { pattern: /add(?:ed|ing)?\s+(?:user|member)/i, action: 'Add user' },
      { pattern: /remov(?:ed|ing)?\s+(?:member|user)/i, action: 'Remove user' },
      { pattern: /creat(?:ed|ing)?\s+(?:user|account)/i, action: 'Create user' },
      { pattern: /delet(?:ed|ing)?\s+(?:user|account)/i, action: 'Delete user' },
      { pattern: /modif(?:ied|ying)?\s+(?:user|account)/i, action: 'Modify user' },
      { pattern: /reset.*password/i, action: 'Reset password' },
      { pattern: /login|sign[- ]?in/i, action: 'Sign in' }
    ];
    
    for (const { pattern, action } of actionPatterns) {
      if (pattern.test(text) && !actions.includes(action)) {
        actions.push(action);
      }
    }
    
    if (actions.length === 0) {
      actions.push('Suspicious activity detected');
    }
    
    return actions;
  }

  extractSuspiciousActivityCount(alert) {
    const text = `${alert.description || ''} ${alert.title || ''}`;
    const countPatterns = [
      /(\d+)\s+(?:suspicious|sensitive|unusual)\s+(?:operations?|activities?)/i,
      /performed\s+(\d+)/i
    ];
    
    for (const pattern of countPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) return parseInt(match[1]);
    }
    
    if (alert.evidence?.length) return alert.evidence.length;
    if (alert.entities?.length) return alert.entities.length;
    return 1;
  }

  groupIncidentsByID(incidents) {
    const incidentGroups = new Map();
    
    incidents.forEach(incident => {
      const incidentId = incident.incidentId || incident.id;
      
      if (!incidentGroups.has(incidentId)) {
        incidentGroups.set(incidentId, {
          ...incident,
          alerts: [incident],
          alertsCount: 1,
          activeAlerts: incident.status === 'New' || incident.status === 'Active' ? 1 : 0,
          activeAlertsRatio: '1/1'
        });
      } else {
        const existingIncident = incidentGroups.get(incidentId);
        existingIncident.alerts.push(incident);
        existingIncident.alertsCount++;
        if (incident.status === 'New' || incident.status === 'Active') {
          existingIncident.activeAlerts++;
        }
        existingIncident.activeAlertsRatio = `${existingIncident.activeAlerts}/${existingIncident.alertsCount}`;
      }
    });
    
    return Array.from(incidentGroups.values());
  }

  transformIncidents(incidents) {
    return incidents.map(incident => this.transformIncident(incident));
  }

  transformIncident(incident) {
    const title = incident.title || incident.displayName || 'Untitled Incident';
    const description = incident.description || 'No description available';
    const severity = incident.severity || 'Informational';
    const status = incident.status || 'Unknown';
    const createdTime = incident.createdDateTime || new Date().toISOString();
    
    const totalAlerts = incident.alerts?.length || 0;
    const activeAlerts = incident.alerts?.filter(alert => 
      alert.status === 'new' || alert.status === 'active'
    ).length || 0;
    const activeAlertsRatio = totalAlerts > 0 ? `${activeAlerts}/${totalAlerts}` : '0/0';
    
    return {
      id: incident.id || `incident-${Date.now()}`,
      incidentId: incident.id || `incident-${Date.now()}`,
      title: title,
      severity: this.mapSeverity(severity),
      status: this.mapStatus(status),
      createdTime: createdTime,
      description: description,
      incidentNumber: incident.id || 'N/A',
      alertsCount: totalAlerts,
      activeAlerts: activeAlerts,
      activeAlertsRatio: activeAlertsRatio,
      owner: incident.assignedTo || 'Unassigned',
      classification: incident.classification || 'Unclassified',
      lastActivityTime: incident.lastUpdateDateTime || createdTime,
      lastUpdateTime: incident.lastUpdateDateTime || createdTime,
      source: 'microsoft-defender'
    };
  }

  mapSeverity(severity) {
    if (typeof severity === 'string') {
      const map = {
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low',
        'informational': 'Informational',
        'critical': 'Critical'
      };
      return map[severity.toLowerCase()] || 'Informational';
    }
    return 'Informational';
  }

  mapStatus(status) {
    if (typeof status === 'string') {
      const map = {
        'new': 'New',
        'active': 'Active',
        'resolved': 'Closed',
        'closed': 'Closed'
      };
      return map[status.toLowerCase()] || 'Unknown';
    }
    return 'Unknown';
  }

  async testConnection() {
    try {
      const url = `${this.baseUrl}/incidents?$top=1`;
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('Connection test failed');
      const data = await response.json();
      return { success: true, incidentCount: data.value?.length || 0 };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

// ==================== INITIALIZE SERVICES ====================

const oauthService = new SentinelOAuthService();
const authService = new SentinelAuthService();

// ==================== MIDDLEWARE ====================

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false }
}));

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// ==================== HELPER FUNCTIONS ====================

async function getUserAccessToken(req) {
  try {
    if (req.session.sentinelAccessToken && req.session.sentinelTokenExpiry) {
      const now = Date.now();
      const expiresIn = req.session.sentinelTokenExpiry - now;
      
      if (expiresIn > 300000) return req.session.sentinelAccessToken;
      
      if (req.session.sentinelRefreshToken) {
        if (req.session.authMethod === 'credentials') {
          return await refreshCredentialToken(req);
        } else {
          return await refreshAccessToken(req);
        }
      }
    }
    throw new Error('No valid access token available');
  } catch (error) {
    console.error('Error getting user access token:', error.message);
    throw error;
  }
}

async function refreshAccessToken(req) {
  try {
    const tokenResponse = await oauthService.refreshAccessToken(req.session.sentinelRefreshToken);
    const { access_token, refresh_token, expires_in } = tokenResponse;
    
    req.session.sentinelAccessToken = access_token;
    req.session.sentinelRefreshToken = refresh_token || req.session.sentinelRefreshToken;
    req.session.sentinelTokenExpiry = Date.now() + (expires_in * 1000);
    
    return access_token;
  } catch (error) {
    throw error;
  }
}

async function refreshCredentialToken(req) {
  try {
    const tokenResponse = await authService.refreshToken(req.session.sentinelRefreshToken);
    
    if (tokenResponse.success) {
      req.session.sentinelAccessToken = tokenResponse.accessToken;
      req.session.sentinelRefreshToken = tokenResponse.refreshToken;
      req.session.sentinelTokenExpiry = tokenResponse.tokenExpiry;
      return tokenResponse.accessToken;
    } else {
      throw new Error(tokenResponse.error);
    }
  } catch (error) {
    throw error;
  }
}

// ==================== ROUTES ====================

app.get('/', (req, res) => {
  res.render('index');
});

app.get('/integrations', (req, res) => {
  res.render('integrations', {
    isSentinelConnected: req.session.isSentinelConnected || false,
    userInfo: req.session.userInfo || null,
    query: req.query
  });
});

app.get('/auth/sentinel', (req, res) => {
  try {
    const state = oauthService.generateRandomState();
    req.session.oauthState = state;
    const authUrl = oauthService.getAuthorizationUrl(state);
    res.redirect(authUrl);
  } catch (error) {
    res.status(500).send('Error initiating authentication');
  }
});

app.get('/auth/sentinel/callback', async (req, res) => {
  const { code, state, error } = req.query;
  
  if (error) return res.redirect('/integrations?error=' + encodeURIComponent(error));
  if (!oauthService.verifyState(state, req.session.oauthState)) {
    return res.status(400).send('Invalid state parameter');
  }
  if (!code) return res.status(400).send('Authorization code not found');
  
  try {
    const tokenResponse = await oauthService.exchangeCodeForToken(code);
    const { access_token, refresh_token, expires_in, id_token } = tokenResponse;
    
    req.session.sentinelAccessToken = access_token;
    req.session.sentinelRefreshToken = refresh_token;
    req.session.sentinelTokenExpiry = Date.now() + (expires_in * 1000);
    req.session.isSentinelConnected = true;
    req.session.authMethod = 'oauth';
    req.session.lastConnected = new Date().toISOString();
    
    if (id_token) {
      const payload = JSON.parse(Buffer.from(id_token.split('.')[1], 'base64').toString());
      req.session.userInfo = {
        displayName: payload.name || payload.preferred_username,
        userPrincipalName: payload.preferred_username || payload.email,
        id: payload.oid || payload.sub
      };
    }
    
    res.redirect('/integrations?connected=sentinel');
  } catch (error) {
    res.redirect('/integrations?error=' + encodeURIComponent('Authentication failed'));
  }
});

app.get('/auth/sentinel/disconnect', (req, res) => {
  req.session.isSentinelConnected = false;
  delete req.session.sentinelAccessToken;
  delete req.session.sentinelRefreshToken;
  delete req.session.sentinelTokenExpiry;
  delete req.session.userInfo;
  res.redirect('/integrations?disconnected=sentinel');
});

app.get('/api/sentinel/alerts', async (req, res) => {
  try {
    if (!req.session.isSentinelConnected) {
      return res.status(401).json({ error: 'Not connected to Microsoft Defender' });
    }

    const accessToken = await getUserAccessToken(req);
    const defenderApi = new DefenderAPIService(accessToken);

    const filters = {};
    if (req.query.severity) filters.severity = req.query.severity;
    if (req.query.status) filters.status = req.query.status;
    if (req.query.includeAll === 'true') filters.includeAll = true;

    const incidents = await defenderApi.getIncidents(filters);

    res.json({
      success: true,
      alerts: incidents,
      totalCount: incidents.length,
      lastUpdated: new Date().toISOString(),
      source: 'microsoft-defender'
    });
  } catch (error) {
    res.status(500).json({ 
      error: 'Failed to fetch incidents',
      details: error.message
    });
  }
});

app.get('/api/sentinel/stats', async (req, res) => {
  try {
    if (!req.session.isSentinelConnected) {
      return res.status(401).json({ error: 'Not connected to Microsoft Defender' });
    }

    const accessToken = await getUserAccessToken(req);
    const defenderApi = new DefenderAPIService(accessToken);

    const activeIncidents = await defenderApi.getIncidents();
    const allIncidents = await defenderApi.getIncidents({ includeAll: true });
    
    const stats = {
      total: activeIncidents.length,
      critical: activeIncidents.filter(a => a.severity === 'Critical').length,
      high: activeIncidents.filter(a => a.severity === 'High').length,
      medium: activeIncidents.filter(a => a.severity === 'Medium').length,
      low: activeIncidents.filter(a => a.severity === 'Low').length,
      bySeverity: {
        critical: activeIncidents.filter(a => a.severity === 'Critical').length,
        high: activeIncidents.filter(a => a.severity === 'High').length,
        medium: activeIncidents.filter(a => a.severity === 'Medium').length,
        low: activeIncidents.filter(a => a.severity === 'Low').length
      }
    };

    res.json({
      success: true,
      stats: stats,
      lastUpdated: new Date().toISOString(),
      source: 'microsoft-defender'
    });
  } catch (error) {
    res.status(500).json({ 
      error: 'Failed to fetch statistics',
      details: error.message
    });
  }
});

app.get('/api/sentinel/incident/:incidentId', async (req, res) => {
  try {
    if (!req.session.isSentinelConnected) {
      return res.status(401).json({ error: 'Not connected to Microsoft Defender' });
    }

    const accessToken = await getUserAccessToken(req);
    const defenderApi = new DefenderAPIService(accessToken);

    const incident = await defenderApi.getIncident(req.params.incidentId);
    const alerts = await defenderApi.getIncidentAlerts(req.params.incidentId);

    res.json({
      success: true,
      incident: incident,
      alerts: alerts,
      source: 'microsoft-defender'
    });
  } catch (error) {
    res.status(500).json({ 
      error: 'Failed to fetch incident details',
      details: error.message
    });
  }
});

app.post('/api/incidents', async (req, res) => {
  try {
    let incidentData;
    
    if (req.body.properties && req.body.properties.incidentNumber) {
      incidentData = {
        incidentId: req.body.properties.incidentNumber,
        title: req.body.properties.title || 'Untitled Incident',
        severity: req.body.properties.severity || 'Informational',
        description: req.body.properties.description || 'No description available',
        createdTime: req.body.properties.createdTimeUtc || new Date().toISOString(),
        status: req.body.properties.status || 'New',
        source: 'logic-app-webhook',
        receivedAt: new Date().toISOString()
      };
    } else {
      incidentData = {
        incidentId: req.body.incidentId || `webhook-${Date.now()}`,
        title: req.body.title || 'Unknown Incident',
        severity: req.body.severity || 'Informational',
        description: req.body.description || 'No description available',
        createdTime: req.body.createdTime || new Date().toISOString(),
        status: req.body.status || 'New',
        source: 'logic-app-custom',
        receivedAt: new Date().toISOString()
      };
    }

    if (!global.receivedIncidents) global.receivedIncidents = [];
    global.receivedIncidents.push(incidentData);

    res.status(200).json({
      success: true,
      message: 'Incident received',
      incidentId: incidentData.incidentId
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/incidents/received', (req, res) => {
  const incidents = global.receivedIncidents || [];
  res.json({
    success: true,
    totalCount: incidents.length,
    incidents: incidents
  });
});

// ==================== START SERVER ====================

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`Integrations page: http://localhost:${PORT}/integrations`);
});

