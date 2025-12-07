@csrf_exempt
@api_view(['GET'])
@permission_classes([IncidentAnalyticsPermission])
@authentication_classes([])
@rbac_required(required_permission='incident_performance_analytics')
def incident_dashboard(request):
    """
    Endpoint to fetch incident dashboard data
    Returns aggregated metrics, status counts, and summary data for the dashboard
    """
    client_ip = get_client_ip(request)
    user_id = request.GET.get('userId')
    
    # Log dashboard access
    send_log(
        module="Incident",
        actionType="ACCESS_INCIDENT_DASHBOARD",
        description="User accessing incident dashboard",
        userId=str(user_id) if user_id else None,
        userName=request.GET.get('userName', 'Unknown'),
        entityType="Dashboard",
        ipAddress=client_ip
    )
    print("incident_dashboard called")
    
    from django.apps import apps
    from django.db.models import Count, Avg, F, ExpressionWrapper, fields
    from django.http import JsonResponse
    from django.utils import timezone
    import datetime
    
    try:
        # Debug: Log all incoming parameters
        print(f"[DEBUG] All GET parameters: {dict(request.GET)}")
        print(f"[DEBUG] Request path: {request.path}")
        print(f"[DEBUG] Request method: {request.method}")
        
        # Define allowed GET parameters
        allowed_params = {
            'timeRange': {
                'type': 'choice',
                'choices': ['all', '7days', '30days', '90days', '1year'],
                'required': False
            },
            'user_id': {
                'type': 'integer',
                'required': False
            },
            'framework_id': {
                'type': 'integer',
                'required': False
            },
            'category': {
                'type': 'string',
                'required': False
            },
            'priority': {
                'type': 'string',
                'required': False
            }
        }
        
        # Validate GET parameters
        validated_params, error = validate_get_parameters(request, allowed_params)
        if error:
            print(f"[DEBUG] Validation error: {error}")
            return JsonResponse({'success': False, 'message': error}, status=400)
        
        print(f"[DEBUG] Validated parameters: {validated_params}")
        
        # Get the Incident model from the app registry
        Incident = apps.get_model('grc', 'Incident')
        
        # Get time range filter from request (now validated)
        time_range = validated_params.get('timeRange', 'all')
        print(f"Incident dashboard request with timeRange: {time_range}")
        
        # Apply time range filter if specified
        now = timezone.now()
        incidents = Incident.objects.all()
        
        if time_range != 'all':
            if time_range == '7days':
                start_date = now - datetime.timedelta(days=7)
            elif time_range == '30days':
                start_date = now - datetime.timedelta(days=30)
            elif time_range == '90days':
                start_date = now - datetime.timedelta(days=90)
            elif time_range == '1year':
                start_date = now - datetime.timedelta(days=365)
                
            incidents = incidents.filter(CreatedAt__gte=start_date)
        
        # Apply framework filter if provided
        framework_id = request.GET.get('framework_id')
        if framework_id:
            # Filter incidents by framework through compliance relationship
            incidents = incidents.filter(
                ComplianceId__SubPolicy__PolicyId__FrameworkId=framework_id
            )
            print(f"Applied framework filter to dashboard: {framework_id}")
        
        # Apply other filters if provided
        category = request.GET.get('category')
        if category and category != 'All Categories':
            incidents = incidents.filter(RiskCategory=category)
        
        priority = request.GET.get('priority')
        if priority and priority != 'All Priorities':
            incidents = incidents.filter(RiskPriority=priority)
        
        # Debug: Log all unique status values in the database
        unique_statuses = incidents.values_list('Status', flat=True).distinct()
        print(f"[DEBUG] All unique status values in incidents: {list(unique_statuses)}")
        
        # Debug: Log all incidents with their statuses
        all_incidents = incidents.values('IncidentId', 'Status', 'IncidentTitle')[:10]  # First 10 for debugging
        print(f"[DEBUG] Sample incidents with statuses: {list(all_incidents)}")
        
        # Count incidents by status - map actual statuses to dashboard categories
        status_counts = {
            'scheduled': incidents.filter(Status__iexact='Open').count(),  # Open incidents
            'approved': incidents.filter(Status__iexact='Mitigated').count(),  # Mitigated incidents
            'rejected': incidents.filter(Status__iexact='Closed').count()  # Closed incidents
        }
        
        # Debug: Log the counts for each status
        print(f"[DEBUG] Status counts: {status_counts}")
        print(f"[DEBUG] Total incidents count: {incidents.count()}")
        
        # Calculate total count
        total_count = incidents.count()
        
        # Calculate MTTD - Mean Time to Detect
        mttd_incidents = incidents.filter(
            IdentifiedAt__isnull=False,
            CreatedAt__isnull=False
        )
        
        mttd_value = 0
        if mttd_incidents.exists():
            # Calculate in Python to avoid DB-specific functions
            all_incidents = list(mttd_incidents.values('IncidentId', 'CreatedAt', 'IdentifiedAt'))
            total_minutes = 0
            
            for incident in all_incidents:
                created = incident['CreatedAt']
                identified = incident['IdentifiedAt']
                diff_seconds = (identified - created).total_seconds()
                minutes = diff_seconds / 60
                total_minutes += minutes
            
            mttd_value = round(total_minutes / len(all_incidents), 2)
        
        # Calculate resolution rate 
        resolution_rate = 0
        if total_count > 0:
            # Include mitigated incidents as resolved
            resolved_count = status_counts['approved']  # This now contains mitigated incidents
            resolution_rate = round((resolved_count / total_count) * 100, 1)
        
        # Calculate change percentage by comparing with previous 30 days
        change_percentage = 0
        try:
            # Get incidents from the previous 30 days (for comparison)
            previous_start = now - datetime.timedelta(days=60)
            previous_end = now - datetime.timedelta(days=30)
            previous_count = Incident.objects.filter(
                CreatedAt__gte=previous_start,
                CreatedAt__lt=previous_end
            ).count()
            
            # Get current period count (last 30 days)
            current_start = now - datetime.timedelta(days=30)
            current_count = Incident.objects.filter(
                CreatedAt__gte=current_start
            ).count()
            
            # Calculate percentage change
            if previous_count > 0:
                change_percentage = round(((current_count - previous_count) / previous_count) * 100, 1)
            elif current_count > 0:
                change_percentage = 100  # New incidents appeared
            else:
                change_percentage = 0  # No incidents in either period
                
        except Exception as e:
            print(f"Error calculating change percentage: {e}")
            change_percentage = 0
        
        # Prepare response data
        response_data = {
            'success': True,
            'data': {
                'summary': {
                    'status_counts': status_counts,
                    'total_count': total_count,
                    'mttd_value': mttd_value,
                    'mttr_value': 0,  # This would be calculated from resolution times
                    'change_percentage': change_percentage,
                    'resolution_rate': resolution_rate
                }
            }
        }
        
        # Debug: Log the final response
        print(f"[DEBUG] Final response data: {response_data}")
        print(f"[DEBUG] Status counts in response: {response_data['data']['summary']['status_counts']}")
        
        print(f"Returning incident dashboard response")
        
        # Log successful dashboard access
        send_log(
            module="Incident",
            actionType="ACCESS_INCIDENT_DASHBOARD_SUCCESS",
            description="Successfully retrieved incident dashboard data",
            userId=str(user_id) if user_id else None,
            userName=request.GET.get('userName', 'Unknown'),
            entityType="Dashboard",
            ipAddress=client_ip,
            additionalInfo={
                "total_incidents": total_count,
                "time_range": time_range,
                "status_counts": status_counts
            }
        )
        
    except Exception as e:
        print(f"Error in incident_dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log dashboard error
        send_log(
            module="Incident",
            actionType="ACCESS_INCIDENT_DASHBOARD_ERROR",
            description=f"Error retrieving incident dashboard data: {str(e)}",
            userId=str(user_id) if user_id else None,
            userName=request.GET.get('userName', 'Unknown'),
            entityType="Dashboard",
            logLevel="ERROR",
            ipAddress=client_ip,
            additionalInfo={"error": str(e)}
        )
        
        # Return an error response
        response_data = {
            'success': False,
            'message': f"Error fetching incident dashboard data: {str(e)}",
            'data': {
                'summary': {
                    'status_counts': {
                        'scheduled': 0, 
                        'approved': 0,
                        'rejected': 0
                    },
                    'total_count': 0,
                    'mttd_value': 0,
                    'mttr_value': 0,
                    'change_percentage': 0,
                    'resolution_rate': 0
                }
            }
        }
    
    return JsonResponse(response_data)
@csrf_exempt
@api_view(['POST'])
@permission_classes([IncidentAnalyticsPermission])
@authentication_classes([])
@rbac_required(required_permission='incident_performance_analytics')
def incident_analytics(request):
    """
    Endpoint to fetch incident analytics data for charts based on specified dimensions
    Returns chart data structured for Chart.js display
    """
    # RBAC Debug - Log user access attempt (temporarily disabled)
    # debug_info = debug_user_permissions(request, "VIEW_INCIDENT_ANALYTICS", "incident", None)
    
    print("incident_analytics called")
    
    from django.apps import apps
    from django.db.models import Count
    from django.db.models.functions import TruncDate, TruncMonth, TruncQuarter
    from django.http import JsonResponse
    from django.utils import timezone
    import json
    
    try:
        # Define validation rules for analytics request
        validation_rules = {
            'xAxis': {
                'type': 'choice',
                'choices': ['Time', 'Date', 'Month', 'Quarter'],
                'required': False
            },
            'yAxis': {
                'type': 'choice',
                'choices': ['Severity', 'Status', 'Origin', 'RiskCategory', 'RiskPriority', 'Repeated', 'CostImpact'],
                'required': False
            },
            'timeRange': {
                'type': 'choice',
                'choices': ['all', '7days', '30days', '90days', '1year'],
                'required': False
            },
            'chartType': {
                'type': 'choice',
                'choices': ['bar', 'line', 'pie', 'doughnut', 'radar'],
                'required': False
            },
            'filters': {
                'type': 'string',  # JSON object as string
                'required': False
            }
        }
        
        # Validate JSON request body
        try:
            validated_data = validate_json_request_body(request, validation_rules)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': f'Validation error: {str(e)}',
                'chartData': {'labels': [], 'datasets': [{'label': 'Error', 'data': []}]}
            }, status=400)
        
        # Get validated parameters with defaults
        x_axis = validated_data.get('xAxis', 'Time')
        y_axis = validated_data.get('yAxis', 'Severity')
        time_range = validated_data.get('timeRange', 'all')
        chart_type = validated_data.get('chartType', 'bar')
        filters = validated_data.get('filters', '{}')
        
        # Parse filters if provided
        if isinstance(filters, str):
            try:
                filters = json.loads(filters)
            except json.JSONDecodeError:
                filters = {}
        elif not isinstance(filters, dict):
            filters = {}
        
        # Get the Incident model from the app registry
        Incident = apps.get_model('grc', 'Incident')
        
        print(f"Incident analytics request with xAxis: {x_axis}, yAxis: {y_axis}, timeRange: {time_range}")
        
        # Apply time range filter if specified
        now = timezone.now()
        incidents = Incident.objects.all()
        
        # Debug: Log total incidents before filtering
        print(f"Total incidents before filtering: {incidents.count()}")
        
        if time_range != 'all':
            if time_range == '7days':
                start_date = now - datetime.timedelta(days=7)
            elif time_range == '30days':
                start_date = now - datetime.timedelta(days=30)
            elif time_range == '90days':
                start_date = now - datetime.timedelta(days=90)
            elif time_range == '1year':
                start_date = now - datetime.timedelta(days=365)
                
            incidents = incidents.filter(CreatedAt__gte=start_date)
        
        # Apply framework filter if provided
        framework_id = request.data.get('frameworkId')
        if framework_id:
            # Filter incidents by framework through compliance relationship
            incidents = incidents.filter(
                ComplianceId__SubPolicy__PolicyId__FrameworkId=framework_id
            )
            print(f"Applied framework filter: {framework_id}")
        
        # Apply other filters if provided
        category = request.data.get('category')
        if category and category != 'All Categories':
            incidents = incidents.filter(RiskCategory=category)
        
        priority = request.data.get('priority')
        if priority and priority != 'All Priorities':
            incidents = incidents.filter(RiskPriority=priority)
        
        # Set up chart data based on X-axis selection
        chart_data = {'labels': [], 'datasets': [{'data': []}]}
        
        # Process X-axis dimension first
        if x_axis == 'Date':
            # Group by Date
            date_incidents = (
                incidents
                .annotate(date=TruncDate('CreatedAt'))
                .values('date')
                .annotate(count=Count('IncidentId'))
                .order_by('date')
            )
            
            # Get dates and base counts
            dates = []
            counts = {}
            
            for item in date_incidents:
                if item['date']:
                    date_str = item['date'].strftime('%Y-%m-%d')
                    dates.append(date_str)
                    counts[date_str] = item['count']
            
            chart_data['labels'] = dates
            
        elif x_axis == 'Month':
            # Group by Month
            month_incidents = (
                incidents
                .annotate(month=TruncMonth('CreatedAt'))
                .values('month')
                .annotate(count=Count('IncidentId'))
                .order_by('month')
            )
            
            # Get months and base counts
            months = []
            counts = {}
            
            for item in month_incidents:
                if item['month']:
                    month_str = item['month'].strftime('%b %Y')
                    months.append(month_str)
                    counts[month_str] = item['count']
            
            chart_data['labels'] = months
            
        elif x_axis == 'Quarter':
            # Group by Quarter
            quarter_incidents = (
                incidents
                .annotate(quarter=TruncQuarter('CreatedAt'))
                .values('quarter')
                .annotate(count=Count('IncidentId'))
                .order_by('quarter')
            )
            
            # Get quarters and base counts
            quarters = []
            counts = {}
            
            for item in quarter_incidents:
                if item['quarter']:
                    year = item['quarter'].year
                    # Calculate quarter number (1-4)
                    quarter_num = (item['quarter'].month - 1) // 3 + 1
                    quarter_str = f"Q{quarter_num} {year}"
                    quarters.append(quarter_str)
                    counts[quarter_str] = item['count']
            
            chart_data['labels'] = quarters
            
        else:
            # Default 'Time' x-axis - Just count incidents without time dimension
            # We'll fill this in based on the Y-axis selection
            pass
        
        # Process Y-axis dimension
        if y_axis == 'Severity':
            # Group by RiskPriority (severity)
            severity_levels = ['High', 'Medium', 'Low']
            
            if x_axis == 'Time':
                # Just show total counts by severity
                all_incidents = list(incidents.values('IncidentId', 'RiskPriority'))
                
                # Initialize counters
                severity_counts = {'High': 0, 'Medium': 0, 'Low': 0}
                
                # Count by severity
                for incident in all_incidents:
                    priority = incident['RiskPriority']
                    if not priority:
                        continue
                    
                    # Map to standard priority buckets
                    standard_priority = 'Medium'  # Default
                    priority_lower = priority.lower()
                    
                    if 'high' in priority_lower:
                        standard_priority = 'High'
                    elif 'low' in priority_lower:
                        standard_priority = 'Low'
                    
                    severity_counts[standard_priority] += 1
                
                # Prepare chart data
                chart_data['labels'] = list(severity_counts.keys())
                chart_data['datasets'][0]['data'] = list(severity_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Severity'
            else:
                # We're grouping by a time dimension (Date, Month, Quarter)
                # Need to create a dataset for each severity level
                datasets = []
                
                # Create a dataset for each severity level
                for severity in severity_levels:
                    # Count incidents of this severity for each time period
                    severity_data = []
                    
                    for label in chart_data['labels']:
                        # Get incidents for this time period
                        period_incidents = 0
                        
                        # Logic to filter incidents by time period and severity
                        # This will depend on the time dimension (date, month, quarter)
                        # For simplicity, we'll use placeholder data
                        period_incidents = counts.get(label, 0) // 3  # Distribute roughly equally
                        
                        severity_data.append(period_incidents)
                    
                    # Create dataset for this severity
                    datasets.append({
                        'label': f'{severity} Severity',
                        'data': severity_data,
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',  # You'll need to set appropriate colors
                        'borderColor': 'rgb(255, 99, 132)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'Status':
            # Group by Status - map actual statuses to dashboard categories
            if x_axis == 'Time':
                # Count by status - map actual statuses to dashboard categories
                status_counts = {
                    'Scheduled': incidents.filter(Status__iexact='Open').count(),  # Open incidents
                    'Approved': incidents.filter(Status__iexact='Mitigated').count(),  # Mitigated incidents
                    'Rejected': incidents.filter(Status__iexact='Closed').count()  # Closed incidents
                }
                
                # Debug: Log status counts
                print(f"Status counts for chart: {status_counts}")
                
                # Prepare chart data
                chart_data['labels'] = list(status_counts.keys())
                chart_data['datasets'][0]['data'] = list(status_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Status'
            else:
                # We're grouping by a time dimension (Date, Month, Quarter)
                # Need to create a dataset for each status
                datasets = []
                
                # Create a dataset for each status - map actual statuses to dashboard categories
                status_mapping = [
                    ('Scheduled', 'Open'),
                    ('Approved', 'Mitigated'), 
                    ('Rejected', 'Closed')
                ]
                
                for display_status, actual_status in status_mapping:
                    # Count incidents of this status for each time period
                    status_data = []
                    
                    for label in chart_data['labels']:
                        # Get incidents for this time period and status
                        period_incidents = 0
                        
                        # Logic to filter incidents by time period and status
                        # This will depend on the time dimension (date, month, quarter)
                        # For simplicity, we'll use placeholder data
                        period_incidents = counts.get(label, 0) // 3  # Distribute roughly equally
                        
                        status_data.append(period_incidents)
                    
                    # Create dataset for this status
                    datasets.append({
                        'label': f'{display_status} Status',
                        'data': status_data,
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',  # You'll need to set appropriate colors
                        'borderColor': 'rgb(54, 162, 235)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'Origin':
            # Group by Origin
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'Origin'))
                
                # Initialize counters for specific origins
                origin_counts = {'Manual': 0, 'SIEM': 0, 'Audit Finding': 0, 'Other': 0}
                
                # Count by origin
                for incident in all_incidents:
                    origin = incident['Origin']
                    if not origin:
                        continue
                    
                    # Map to standard origin buckets
                    if origin in origin_counts:
                        origin_counts[origin] += 1
                    else:
                        origin_counts['Other'] += 1
                
                # Remove 'Other' category if it's empty
                if origin_counts['Other'] == 0:
                    del origin_counts['Other']
                
                # Prepare chart data
                chart_data['labels'] = list(origin_counts.keys())
                chart_data['datasets'][0]['data'] = list(origin_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Origin'
            else:
                # We're grouping by a time dimension (Date, Month, Quarter)
                # Need to create a dataset for each origin
                datasets = []
                origins = ['Manual', 'SIEM', 'Audit Finding', 'Other']
                
                # Create a dataset for each origin
                for origin in origins:
                    # Count incidents of this origin for each time period
                    origin_data = []
                    
                    for label in chart_data['labels']:
                        # Logic to filter incidents by time period and origin
                        # For simplicity, we'll use placeholder data
                        period_incidents = counts.get(label, 0) // len(origins)  # Distribute roughly equally
                        origin_data.append(period_incidents)
                    
                    # Create dataset for this origin
                    datasets.append({
                        'label': f'{origin} Origin',
                        'data': origin_data,
                        'backgroundColor': 'rgba(75, 192, 192, 0.5)',  # You'll need to set appropriate colors
                        'borderColor': 'rgb(75, 192, 192)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'RiskCategory':
            # Group by RiskCategory
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'RiskCategory'))
                
                # Initialize counters for risk categories
                category_counts = {}
                
                # Count by category
                for incident in all_incidents:
                    category = incident['RiskCategory']
                    if not category:
                        continue
                    
                    if category in category_counts:
                        category_counts[category] += 1
                    else:
                        category_counts[category] = 1
                
                # Prepare chart data
                chart_data['labels'] = list(category_counts.keys())
                chart_data['datasets'][0]['data'] = list(category_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Risk Category'
            else:
                # Get unique risk categories from the database
                unique_categories = incidents.exclude(RiskCategory__isnull=True).values_list('RiskCategory', flat=True).distinct()
                categories = list(unique_categories)
                
                if not categories:
                    # Fallback to common categories if none found in database
                    categories = ['Security', 'Compliance', 'Operational', 'Financial', 'Strategic']
                
                # We're grouping by a time dimension
                datasets = []
                
                for category in categories:
                    category_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(categories)
                        category_data.append(period_incidents)
                    
                    datasets.append({
                        'label': f'{category} Category',
                        'data': category_data,
                        'backgroundColor': 'rgba(153, 102, 255, 0.5)',
                        'borderColor': 'rgb(153, 102, 255)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'RiskPriority':
            # Group by RiskPriority (similar to Severity but preserving the exact field name)
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'RiskPriority'))
                
                # Initialize counters for priorities
                priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}
                
                # Count by priority
                for incident in all_incidents:
                    priority = incident['RiskPriority']
                    if not priority:
                        continue
                    
                    # Map to standard priority buckets
                    standard_priority = 'Medium'  # Default
                    priority_lower = priority.lower()
                    
                    if 'high' in priority_lower:
                        standard_priority = 'High'
                    elif 'low' in priority_lower:
                        standard_priority = 'Low'
                    
                    priority_counts[standard_priority] += 1
                
                # Remove priorities with zero count
                priority_counts = {k: v for k, v in priority_counts.items() if v > 0}
                
                # Prepare chart data
                chart_data['labels'] = list(priority_counts.keys())
                chart_data['datasets'][0]['data'] = list(priority_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Risk Priority'
            else:
                # We're grouping by a time dimension
                datasets = []
                priorities = ['High', 'Medium', 'Low']
                
                for priority in priorities:
                    priority_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(priorities)
                        priority_data.append(period_incidents)
                    
                    datasets.append({
                        'label': f'{priority} Priority',
                        'data': priority_data,
                        'backgroundColor': 'rgba(255, 159, 64, 0.5)',
                        'borderColor': 'rgb(255, 159, 64)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'Repeated':
            # Group by RepeatedNot field (0 = Not repeated, 1 = Repeated)
            if x_axis == 'Time':
                # Initialize counters
                repeated_counts = {'Not Repeated': 0, 'Repeated': 0}
                
                # Count by repeated status
                for incident in incidents:
                    repeated = incident.RepeatedNot
                    if repeated == 1:
                        repeated_counts['Repeated'] += 1
                    else:
                        repeated_counts['Not Repeated'] += 1
                
                # Prepare chart data
                chart_data['labels'] = list(repeated_counts.keys())
                chart_data['datasets'][0]['data'] = list(repeated_counts.values())
                chart_data['datasets'][0]['label'] = 'Incidents by Repeated Status'
            else:
                # We're grouping by a time dimension
                datasets = []
                statuses = ['Repeated', 'Not Repeated']
                
                for status in statuses:
                    status_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(statuses)
                        status_data.append(period_incidents)
                    
                    datasets.append({
                        'label': status,
                        'data': status_data,
                        'backgroundColor': 'rgba(201, 203, 207, 0.5)',
                        'borderColor': 'rgb(201, 203, 207)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
            
        elif y_axis == 'CostImpact':
            # Group by cost impact
            if x_axis == 'Time':
                all_incidents = list(incidents.values('IncidentId', 'CostOfIncident'))
                
                # Process numeric cost values
                cost_data = {}
                
                # Count by cost impact
                for incident in all_incidents:
                    cost = incident['CostOfIncident']
                    if not cost:
                        continue
                    
                    # Try to convert to numeric value
                    try:
                        cost_value = float(cost)
                        # Round to nearest 100 for binning
                        cost_bin = round(cost_value / 100) * 100
                        cost_bin_str = str(cost_bin)
                        
                        if cost_bin_str in cost_data:
                            cost_data[cost_bin_str] += 1
                        else:
                            cost_data[cost_bin_str] = 1
                    except (ValueError, TypeError):
                        # If can't convert to number, skip this record
                        continue
                
                # If we have numeric data, use it
                if cost_data:
                    # Sort the cost bins numerically
                    sorted_costs = sorted(cost_data.items(), key=lambda x: float(x[0]))
                    
                    # Prepare chart data with numeric cost values
                    chart_data['labels'] = [cost for cost, _ in sorted_costs]
                    chart_data['datasets'][0]['data'] = [count for _, count in sorted_costs]
                    chart_data['datasets'][0]['label'] = 'Incidents by Cost (₹)'
                else:
                    # Fallback to categorical if no numeric data
                    # Initialize cost impact buckets
                    cost_mapping = {'Low': 0, 'Medium': 0, 'High': 0, 'Unknown': 0}
                    
                    # Count by cost impact
                    for incident in all_incidents:
                        cost = incident['CostOfIncident']
                        if not cost:
                            cost_mapping['Unknown'] += 1
                            continue
                        
                        # Categorize cost (example logic, adjust as needed)
                        if isinstance(cost, str):
                            cost_lower = cost.lower()
                            if 'high' in cost_lower:
                                cost_mapping['High'] += 1
                            elif 'medium' in cost_lower or 'med' in cost_lower:
                                cost_mapping['Medium'] += 1
                            elif 'low' in cost_lower:
                                cost_mapping['Low'] += 1
                            else:
                                cost_mapping['Unknown'] += 1
                        else:
                            # If it's a numeric value
                            try:
                                cost_value = float(cost)
                                if cost_value > 1000:
                                    cost_mapping['High'] += 1
                                elif cost_value > 100:
                                    cost_mapping['Medium'] += 1
                                else:
                                    cost_mapping['Low'] += 1
                            except (ValueError, TypeError):
                                cost_mapping['Unknown'] += 1
                    
                    # Remove 'Unknown' if it's empty
                    if cost_mapping['Unknown'] == 0:
                        del cost_mapping['Unknown']
                    
                    # Prepare chart data
                    chart_data['labels'] = list(cost_mapping.keys())
                    chart_data['datasets'][0]['data'] = list(cost_mapping.values())
                    chart_data['datasets'][0]['label'] = 'Incidents by Cost Impact'
            else:
                # For time-based X-axis, we can't easily bin numeric costs
                # So we'll stick with categories
                datasets = []
                impact_levels = ['Low', 'Medium', 'High']
                
                for level in impact_levels:
                    level_data = []
                    
                    for label in chart_data['labels']:
                        # For simplicity, use placeholder data
                        period_incidents = counts.get(label, 0) // len(impact_levels)
                        level_data.append(period_incidents)
                    
                    datasets.append({
                        'label': f'{level} Cost Impact',
                        'data': level_data,
                        'backgroundColor': 'rgba(255, 205, 86, 0.5)',
                        'borderColor': 'rgb(255, 205, 86)',
                        'borderWidth': 1
                    })
                
                chart_data['datasets'] = datasets
        else:
            # Default fallback - return incidents by month
            from django.db.models.functions import TruncMonth
            
            # Group by month
            monthly_incidents = (
                incidents
                .annotate(month=TruncMonth('CreatedAt'))
                .values('month')
                .annotate(count=Count('IncidentId'))
                .order_by('month')
            )
            
            # Format for chart
            months = []
            counts = []
            
            for item in monthly_incidents:
                if item['month']:
                    months.append(item['month'].strftime('%b %Y'))
                    counts.append(item['count'])
            
            # Prepare chart data
            chart_data['labels'] = months
            chart_data['datasets'][0]['data'] = counts
            chart_data['datasets'][0]['label'] = 'Incidents by Month'
        
        # Calculate approval rate for the dashboard
        total_count = incidents.count()
        approved_count = incidents.filter(Status__iexact='Approved').count()
        approval_rate = 0
        
        if total_count > 0:
            approval_rate = round((approved_count / total_count) * 100, 1)
        
        # Prepare response data
        response_data = {
            'success': True,
            'chartData': chart_data,
            'dashboardData': {
                'approval_rate': approval_rate
            }
        }
        
        print(f"Returning incident analytics response")
        print(f"Chart data: {chart_data}")
        print(f"Response data: {response_data}")
        
    except Exception as e:
        print(f"Error in incident_analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return an error response with empty chart data
        response_data = {
            'success': False,
            'message': f"Error fetching incident analytics data: {str(e)}",
            'chartData': {
                'labels': [],
                'datasets': [{
                    'label': 'Error',
                    'data': []
                }]
            },
            'dashboardData': {
                'approval_rate': 0
            }
        }
    
    return JsonResponse(response_data)

@api_view(['GET'])
@authentication_classes([])
@permission_classes([IncidentViewPermission])
@rbac_required(required_permission='view_all_incident')
def get_recent_incidents(request):
    """
    Endpoint to fetch recent incidents for the dashboard activity feed
    Returns the most recent incidents with their details
    """
    # RBAC Debug - Log user access attempt
    debug_info = debug_user_permissions(request, "VIEW_RECENT_INCIDENTS", "incident", None)
    
    print("get_recent_incidents called")
    
    from django.apps import apps
    from django.http import JsonResponse
    
    try:
        # Debug: Log all incoming parameters
        print(f"[DEBUG] get_recent_incidents - All GET parameters: {dict(request.GET)}")
        print(f"[DEBUG] get_recent_incidents - Request path: {request.path}")
        print(f"[DEBUG] get_recent_incidents - Request method: {request.method}")
        
        # Define allowed GET parameters
        allowed_params = {
            'limit': {
                'type': 'integer',
                'min_value': 1,
                'max_value': 100,
                'required': False
            },
            'user_id': {
                'type': 'integer',
                'required': False
            }
        }
        
        # Validate GET parameters
        validated_params, error = validate_get_parameters(request, allowed_params)
        if error:
            print(f"[DEBUG] get_recent_incidents - Validation error: {error}")
            return JsonResponse({'success': False, 'message': error}, status=400)
        
        print(f"[DEBUG] get_recent_incidents - Validated parameters: {validated_params}")
        
        # Get the Incident model from the app registry
        Incident = apps.get_model('grc', 'Incident')
        
        # Get limit parameter (default to 3)
        limit = validated_params.get('limit', 3)
        
        # Get the most recent incidents
        recent_incidents = Incident.objects.all().order_by('-CreatedAt')[:limit]
        
        # Convert to list of dictionaries
        incidents_data = []
        for incident in recent_incidents:
            incidents_data.append({
                'IncidentId': incident.IncidentId,
                'IncidentTitle': incident.IncidentTitle,
                'Description': incident.Description,
                'RiskPriority': incident.RiskPriority,
                'Status': incident.Status,
                'CreatedAt': incident.CreatedAt,
                'Origin': incident.Origin
            })
        
        # Prepare response data
        response_data = {
            'success': True,
            'incidents': incidents_data
        }
        
        print(f"Returning {len(incidents_data)} recent incidents")
        
    except Exception as e:
        print(f"Error in get_recent_incidents: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return an error response
        response_data = {
            'success': False,
            'message': f"Error fetching recent incidents: {str(e)}",
            'incidents': []
        }
    
    return JsonResponse(response_data)