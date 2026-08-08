from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class UserIssueResolverAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create different user roles
        self.superuser = User.objects.create_superuser(username='admin', password='adminpassword')
        self.staff_user = User.objects.create_user(username='staff', password='staffpassword', is_staff=True)
        self.regular_user = User.objects.create_user(username='user', password='userpassword')

    def test_public_landing_page_redirects(self):
        """Landing root URL redirects users to the user submit page."""
        response = self.client.get(reverse('landing'))
        self.assertRedirects(response, reverse('user_portal'))

    def test_user_portal_accessible_anonymous(self):
        """Anonymous requests can access the user submit portal."""
        response = self.client.get(reverse('user_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'What issue are you facing?')

    def test_developer_dashboard_redirects_anonymous(self):
        """Anonymous requests to developer dashboard redirect to login page."""
        response = self.client.get(reverse('developer_dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('developer_dashboard')}")

    def test_login_page_renders(self):
        """Login page displays correctly."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In to User Issue Resolver')

    def test_user_login_success_with_superuser(self):
        """Superusers can log in to the User Portal successfully."""
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'adminpassword',
            'role': 'user'
        })
        self.assertRedirects(response, reverse('user_portal'))

    def test_user_login_fails_with_staff_user(self):
        """Staff-only users cannot access the User Portal."""
        response = self.client.post(reverse('login'), {
            'username': 'staff',
            'password': 'staffpassword',
            'role': 'user'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User portal requires authorized credentials')

    def test_developer_login_success_with_staff_user(self):
        """Staff users can access the Developer Dashboard."""
        response = self.client.post(reverse('login'), {
            'username': 'staff',
            'password': 'staffpassword',
            'role': 'developer'
        })
        self.assertRedirects(response, reverse('developer_dashboard'))

    def test_developer_login_fails_with_regular_user(self):
        """Regular users cannot access the Developer Dashboard."""
        response = self.client.post(reverse('login'), {
            'username': 'user',
            'password': 'userpassword',
            'role': 'developer'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Developer portal requires admin privileges')

    def test_invalid_credentials(self):
        """Invalid username/password combinations display error message."""
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'wrongpassword',
            'role': 'developer'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials or insufficient permissions')

    def test_logout_redirects_to_landing(self):
        """Logout action clears session and redirects to landing root."""
        # Log in first
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('logout'))
        # redirects to landing root, which redirects to user_portal
        self.assertRedirects(response, reverse('landing'), target_status_code=302)

    def test_signup_creates_regular_user(self):
        """New user accounts can register and are auto-logged in."""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@user.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword'
        })
        self.assertRedirects(response, reverse('user_portal'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_analytics_redirects_anonymous(self):
        """Anonymous requests to analytics page redirect to login."""
        response = self.client.get(reverse('analytics'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('analytics')}")

    def test_analytics_blocked_for_regular_user(self):
        """Regular user users are redirected away from the analytics page."""
        self.client.login(username='user', password='userpassword')
        response = self.client.get(reverse('analytics'))
        self.assertRedirects(response, reverse('user_portal'))

    def test_analytics_accessible_for_staff_user(self):
        """Staff/superuser accounts can successfully view the analytics page."""
        self.client.login(username='staff', password='staffpassword')
        response = self.client.get(reverse('analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')

    def test_team_queue_redirects_anonymous(self):
        """Anonymous requests to team queue page redirect to login."""
        response = self.client.get(reverse('team_queue'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('team_queue')}")

    def test_team_queue_blocked_for_regular_user(self):
        """Regular user users are redirected away from the team queue page."""
        self.client.login(username='user', password='userpassword')
        response = self.client.get(reverse('team_queue'))
        self.assertRedirects(response, reverse('user_portal'))

    def test_team_queue_accessible_for_staff_user(self):
        """Staff/superuser accounts can successfully view the team queue page."""
        self.client.login(username='staff', password='staffpassword')
        response = self.client.get(reverse('team_queue'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team Queues')

    def test_update_issue_assigned_team(self):
        """Updating assigned team via POST on issue details page persists correctly."""
        from issues.models import Issue
        issue = Issue.objects.create(
            subject='Urgent issue',
            body='Crash report',
            assigned_team='General Inquiry'
        )
        self.client.login(username='staff', password='staffpassword')
        response = self.client.post(reverse('issue_detail', args=[issue.id]), {
            'assigned_team': 'Technical Support',
            'status': 'Open',
            'urgency_score': 'High',
            'sentiment_score': '0.5'
        })
        self.assertRedirects(response, reverse('issue_detail', args=[issue.id]))
        issue.refresh_from_db()
        self.assertEqual(issue.assigned_team, 'Technical Support')

    def test_download_excel_redirects_anonymous(self):
        """Anonymous requests to Excel download endpoint redirect to login."""
        response = self.client.get(reverse('download_issues_excel'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('download_issues_excel')}")

    def test_download_excel_blocked_for_regular_user(self):
        """Regular user users are redirected away from the Excel download endpoint."""
        self.client.login(username='user', password='userpassword')
        response = self.client.get(reverse('download_issues_excel'))
        self.assertRedirects(response, reverse('user_portal'))

    def test_download_excel_accessible_for_staff_user(self):
        """Staff/superuser accounts can successfully download the issues Excel sheet."""
        self.client.login(username='staff', password='staffpassword')
        response = self.client.get(reverse('download_issues_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['content-type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertTrue(response.has_header('Content-Disposition'))
        self.assertIn('attachment', response['Content-Disposition'])

    def test_all_issues_redirects_anonymous(self):
        """Anonymous requests to all issues page redirect to login."""
        response = self.client.get(reverse('all_issues'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('all_issues')}")

    def test_all_issues_blocked_for_regular_user(self):
        """Regular user users are redirected away from the all issues page."""
        self.client.login(username='user', password='userpassword')
        response = self.client.get(reverse('all_issues'))
        self.assertRedirects(response, reverse('user_portal'))

    def test_all_issues_accessible_for_staff_user(self):
        """Staff/superuser accounts can successfully view the all issues page."""
        self.client.login(username='staff', password='staffpassword')
        response = self.client.get(reverse('all_issues'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All Issues')
