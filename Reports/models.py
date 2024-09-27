from django.db import models

# Create your models here.

class report_columns(models.Model):
    id = models.BigAutoField(primary_key=True)
    entity = models.TextField(null=True, blank=True)
    field_name = models.TextField(null=True, blank=True)
    display_name = models.TextField(null=True, blank=True)
    join_name = models.TextField(null=True, blank=True)
    join_clause = models.TextField(null=True, blank=True)
    order = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'report_columns'

class report_filters(models.Model):
    filter_id = models.BigAutoField(primary_key=True)
    entity = models.TextField(null=True, blank=True)
    filter_parameter = models.TextField(null=True, blank=True)
    filter_values = models.TextField(null=True, blank=True)
    from_clause = models.TextField(null=True, blank=True)
    where_clause = models.TextField(null=True, blank=True)
    join_clause = models.TextField(null=True, blank=True)
    group_by = models.TextField(null=True, blank=True)
    order_by = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    is_mandatory = models.TextField(null=True, blank=True)
    order = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'report_filters'
        
class saved_report_filters(models.Model):
    id = models.BigAutoField(primary_key=True)
    saved_name = models.TextField(null=True, blank=True)
    entity = models.TextField(null=True, blank=True)
    filters = models.TextField(null=True, blank=True)
    sub_filters = models.TextField(null=True, blank=True)
    selected_columns = models.TextField(null=True, blank=True)
    filter_count = models.TextField(null=True, blank=True)
    display_names = models.TextField(null=True, blank=True)
    sql_query = models.TextField(null=True, blank=True)
    user_id = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'saved_report_filters'