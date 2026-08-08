from django import forms
from .models import Issue

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['customer_email', 'subject', 'body']
        labels = {
            'customer_email': 'User Email Address',
        }
        widgets = {
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief subject...'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your issue in detail...'}),
        }

    def clean_subject(self):
        subject = self.cleaned_data.get('subject')
        if not subject or len(subject.strip()) < 5:
            raise forms.ValidationError("Subject must be at least 5 characters long.")
        return subject

    def clean_body(self):
        body = self.cleaned_data.get('body')
        if not body or len(body.strip()) < 10:
            raise forms.ValidationError("Body description must be at least 10 characters long.")
        return body
