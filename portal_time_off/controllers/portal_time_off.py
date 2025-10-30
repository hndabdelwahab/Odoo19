from odoo import http
from odoo.http import request


class PortalTimeOff(http.Controller):

    @http.route(['/my/time_off'], type='http', auth="user", website=True)
    def portal_time_off(self, **kwargs):
        """Display all time off requests for the current user"""
        user = request.env.user
        time_offs = request.env['hr.leave'].sudo().search([('employee_id.work_email', '=', user.email)])
        leave_types = request.env['hr.leave.type'].sudo().search([])
        
        return request.render('portal_time_off.portal_time_off_page', {
            'time_offs': time_offs,
            'leave_types': leave_types,
        })

    @http.route(['/my/apply_time_off'], type='http', auth="user", website=True)
    def portal_apply_time_off(self, **kwargs):
        """
        Show the Apply Time Off form with ONLY leave types the employee has allocations for.
        """
        user = request.env.user
        
        # Find employee by user_id or email
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not employee:
            employee = request.env['hr.employee'].sudo().search([('work_email', '=', user.email)], limit=1)
        
        time_off_types = []

        if employee:
            # Get ONLY approved allocations for this employee
            allocations = request.env['hr.leave.allocation'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),  # Only approved
            ])
            
            # Extract leave type IDs
            leave_type_ids = allocations.mapped('holiday_status_id').ids
            
            if leave_type_ids:
                # Get leave types from allocations
                leave_types = request.env['hr.leave.type'].sudo().browse(leave_type_ids)

                for leave_type in leave_types:
                    # Get the allocation for this leave type
                    allocation = allocations.filtered(lambda a: a.holiday_status_id.id == leave_type.id)[0]
                    
                    # Count already used days
                    used_days = request.env['hr.leave'].sudo().search_count([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', 'in', ['validate', 'validate1']),
                    ])
                    
                    # Calculate remaining
                    remaining_leaves = allocation.number_of_days - used_days
                    max_allocation = allocation.number_of_days
                    
                    label = f"{leave_type.name} ({remaining_leaves} remaining out of {max_allocation} days)"

                    time_off_types.append({
                        'id': leave_type.id,
                        'label': label,
                    })

        return request.render('portal_time_off.portal_apply_time_off_form', {
            'time_off_types': time_off_types,
            'csrf_token': request.csrf_token(),
        })

    @http.route(['/my/apply_time_off/submit'], type='http', auth="user", website=True, methods=['POST'])
    def portal_submit_time_off(self, **post):
        """
        Submit a time off request.
        """
        user = request.env.user
        
        # Get employee record
        employee = (
            request.env['hr.employee']
            .with_company(False)
            .sudo()
            .search([('work_email', '=', user.email)], limit=1)
        )

        if not employee:
            return request.redirect('/my/home')

        try:
            # Validate inputs
            leave_type_id = int(post.get('time_off_type'))
            date_from = post.get('date_from')
            date_to = post.get('date_to')
            description = post.get('description', '')

            if not date_from or not date_to:
                return request.redirect('/my/apply_time_off?error=Missing dates')

            # Verify leave type exists
            leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)
            if not leave_type.exists():
                return request.redirect('/my/apply_time_off?error=Invalid leave type')

            # Verify employee has valid allocation if required
            if leave_type.requires_allocation == 'yes':
                allocation = (
                    request.env['hr.leave.allocation']
                    .sudo()
                    .search([
                        ('employee_id', '=', employee.id),
                        ('holiday_status_id', '=', leave_type_id),
                        ('state', '=', 'validate'),
                    ], limit=1)
                )
                if not allocation:
                    return request.redirect('/my/apply_time_off?error=No valid allocation for this leave type')

            # Create the leave request
            leave = (
                request.env['hr.leave']
                .with_company(employee.company_id or False)
                .sudo()
                .create({
                    'holiday_status_id': leave_type_id,
                    'employee_id': employee.id,
                    'request_date_from': date_from,
                    'request_date_to': date_to,
                    'name': description,
                    'state': 'confirm',
                })
            )

            print("Leave request created with ID:", leave.id)
            return request.redirect(f'/my/home?success=Leave request submitted&leave_id={leave.id}')

        except ValueError as e:
            print("Value Error:", str(e))
            return request.redirect('/my/apply_time_off?error=Invalid data format')
        except Exception as e:
            print("Error creating leave request:", str(e))
            return request.redirect(f'/my/apply_time_off?error={str(e)}')

    @http.route(['/my/allocations'], type='http', auth="user", website=True)
    def portal_my_allocations(self, **kwargs):
        """
        Display user's current leave allocations and remaining days.
        Shows ONLY leave types the employee has allocations for.
        """
        user = request.env.user
        
        # Find employee
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not employee:
            employee = request.env['hr.employee'].sudo().search([('work_email', '=', user.email)], limit=1)

        time_off_types = []

        if employee:
            # Get ONLY approved allocations for this employee
            allocations = request.env['hr.leave.allocation'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),  # Only approved
            ], order='id DESC')
            
            for allocation in allocations:
                leave_type = allocation.holiday_status_id
                
                # Count already used days
                used_days = request.env['hr.leave'].sudo().search_count([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'in', ['validate', 'validate1']),
                ])
                
                # Calculate remaining
                remaining_days = allocation.number_of_days - used_days
                
                time_off_types.append({
                    'id': leave_type.id,
                    'leave_name': leave_type.name,
                    'remain_leave': round(remaining_days, 2),
                    'total_leave': round(allocation.number_of_days, 2),
                })

        return request.render('portal_time_off.portal_my_allocations', {
            'employee': employee,
            'allocations': time_off_types,
        })