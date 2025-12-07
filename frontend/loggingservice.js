const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const winston = require('winston');
const Joi = require('joi');

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Winston Logger setup
const logger = winston.createLogger({
  level: 'debug', // capture all levels including debug
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message, meta }) => {
      let metaStr = meta ? JSON.stringify(meta) : '';
      return `${timestamp} [${level.toUpperCase()}] ${message} ${metaStr}`;
    })
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console(),
  ],
});

// Request validation schema
const logSchema = Joi.object({
  userId: Joi.string().optional(),
  userName: Joi.string().optional(),
  userRole: Joi.string().optional(),
  module: Joi.string().required(),       // e.g., Risk, Policy, Compliance
  entityType: Joi.string().optional(),   // e.g., RiskInstance, RiskApproval
  actionType: Joi.string().required(),   // e.g., CREATE, VIEW, UPDATE, DELETE, CLICK
  description: Joi.string().optional(),
  logLevel: Joi.string().valid('INFO', 'WARN', 'ERROR', 'DEBUG').default('INFO'),
  ipAddress: Joi.string().ip({ version: ['ipv4', 'ipv6'] }).optional(),
  additionalInfo: Joi.object().optional(),
});

// Dynamic message builder function
function buildLogMessage(log) {
  const { module, entityType, actionType, userId, userName, userRole, description, additionalInfo } = log;
  let baseMsg = `[${module.toUpperCase()}]`;

  // Compose base message by module
  switch (module.toLowerCase()) {
    case 'risk':
      baseMsg += ' Risk Module -';
      break;
    case 'policy':
      baseMsg += ' Policy Module -';
      break;
    case 'compliance':
      baseMsg += ' Compliance Module -';
      break;
    default:
      baseMsg += ` ${module} Module -`;
  }

  // Append actionType & entityType
  baseMsg += ` Action: ${actionType.toUpperCase()}`;
  if (entityType) baseMsg += ` on ${entityType}`;

  // Append user info
  if (userName) baseMsg += ` by User: ${userName}`;
  if (userRole) baseMsg += ` (Role: ${userRole})`;

  // Append description or additionalInfo details
  if (description) {
    baseMsg += ` | Details: ${description}`;
  } else if (additionalInfo) {
    baseMsg += ` | Details: ${JSON.stringify(additionalInfo)}`;
  }

  return baseMsg;
}

// Logging POST endpoint
app.post('http://15.207.108.158:8000/api/logs', (req, res) => {
  const { error, value } = logSchema.validate(req.body);
  if (error) {
    return res.status(400).json({ error: error.details[0].message });
  }

  const logMsg = buildLogMessage(value);

  // Multi-dimensional switch logic for level + module + actionType

  const level = value.logLevel.toLowerCase();
  const mod = value.module.toLowerCase();
  const action = value.actionType.toLowerCase();

  // Example of combining switch logic
  if (level === 'error') {
    logger.error(logMsg, value);
  } else if (level === 'warn') {
    logger.warn(logMsg, value);
  } else if (level === 'debug') {
    logger.debug(logMsg, value);
  } else {
    // INFO or default
    // Customize behavior based on module and action type
    if (mod === 'risk') {
      switch (action) {
        case 'create':
          logger.info(`${logMsg} [Risk created successfully]`, value);
          break;
        case 'update':
          logger.info(`${logMsg} [Risk updated]`, value);
          break;
        case 'delete':
          logger.warn(`${logMsg} [Risk deleted]`, value);
          break;
        case 'view':
        case 'click':
          logger.debug(`${logMsg} [Risk viewed or clicked]`, value);
          break;
        default:
          logger.info(logMsg, value);
      }
    } else if (mod === 'policy') {
      switch (action) {
        case 'submit':
          logger.info(`${logMsg} [Policy submitted]`, value);
          break;
        case 'approve':
          logger.info(`${logMsg} [Policy approved]`, value);
          break;
        default:
          logger.info(logMsg, value);
      }
    } else {
      // Generic logging for other modules
      logger.info(logMsg, value);
    }
  }

  res.status(200).json({ message: 'Log recorded successfully' });
});

// Health endpoint
app.get('/health', (req, res) => res.json({ status: 'healthy' }));

// Start server
const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Logging service listening on port ${PORT}`));
