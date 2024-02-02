from django.shortcuts import render
from .gns_plots import visualize_data, aggregate_sentiment_by_entity, prepare_sentiment_data_for_visualization, get_top_positive_entities, prepare_positive_entities_data_for_visualization, get_top_negative_entities, prepare_negative_entities_data_for_visualization
from django.core.cache import cache
from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse
from plotly.offline import plot
import plotly.graph_objs as go

def dashboard(request):
    # Attempt to get cached visualizations
    visualizations = cache.get('dashboard_visualizations')

    if not visualizations:
        # If not cached, generate visualizations
        visualizations = visualize_data()

        # Store the visualizations in the cache for 15 minutes (900 seconds)
        cache.set('dashboard_visualizations', visualizations, 900)

    return render(request, 'dashboard.html', {'visualizations': visualizations})

def sentiment_distribution_view(request):
    aggregated_data = aggregate_sentiment_by_entity()
    df = prepare_sentiment_data_for_visualization(aggregated_data)
    
    fig = go.Figure(data=[
        go.Bar(name='Positive', x=df[df['Sentiment'] == 'Positive']['Entity'], y=df[df['Sentiment'] == 'Positive']['Count']),
        go.Bar(name='Negative', x=df[df['Sentiment'] == 'Negative']['Entity'], y=df[df['Sentiment'] == 'Negative']['Count'])
    ])
    
    fig.update_layout(barmode='group', title='Sentiment Distribution Across Entities')
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)

    return render(request, "sentiment_distribution.html", context={'plot_div': plot_div})


def top_positive_entities_view(request):
    aggregated_data = get_top_positive_entities()
    entities, counts = prepare_positive_entities_data_for_visualization(aggregated_data)
    
    fig = go.Figure([go.Bar(x=entities, y=counts)])
    fig.update_layout(title='Top 10 Entities with Positive Sentiment', xaxis_title='Entity', yaxis_title='Count')
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)

    return render(request, "top_positive_entities.html", context={'plot_div': plot_div})


def top_negative_entities_view(request):
    aggregated_data = get_top_negative_entities()
    entities, counts = prepare_negative_entities_data_for_visualization(aggregated_data)
    
    fig = go.Figure([go.Bar(x=entities, y=counts)])
    fig.update_layout(title='Top 10 Entities with Negative Sentiment', xaxis_title='Entity', yaxis_title='Count')
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)

    return render(request, "top_negative_entities.html", context={'plot_div': plot_div})
